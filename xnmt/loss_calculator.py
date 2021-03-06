import dynet as dy
import numpy as np

from xnmt.loss import LossBuilder
from xnmt.serialize.serializer import Serializable
from xnmt.vocab import Vocab
from xnmt.serialize.tree_tools import Ref, Path
import xnmt.evaluator
import xnmt.linear as linear


class LossCalculator(Serializable):
  '''
  A template class implementing the training strategy and corresponding loss calculation.
  '''
  yaml_tag = '!LossCalculator'

  def __init__(self, loss_calculator = None):
    if loss_calculator is None:
      self.loss_calculator = MLELoss()
    else:
      self.loss_calculator = loss_calculator

  def __call__(self, translator, dec_state, src, trg):
      return self.loss_calculator(translator, dec_state, src, trg)


class MLELoss(Serializable):
  yaml_tag = '!MLELoss'
  
  # TODO: document me

  def __call__(self, translator, dec_state, src, trg):
    trg_mask = trg.mask if xnmt.batcher.is_batched(trg) else None
    losses = []
    seq_len = len(trg[0]) if xnmt.batcher.is_batched(src) else len(trg)
    if xnmt.batcher.is_batched(src):
      for j, single_trg in enumerate(trg):
        assert len(single_trg) == seq_len # assert consistent length
        assert 1==len([i for i in range(seq_len) if (trg_mask is None or trg_mask.np_arr[j,i]==0) and single_trg[i]==Vocab.ES]) # assert exactly one unmasked ES token
    err_rate=0
    for i in range(seq_len):
      ref_word = trg[i] if not xnmt.batcher.is_batched(src) \
                      else xnmt.batcher.mark_as_batch([single_trg[i] for single_trg in trg])

      dec_state.context = translator.attender.calc_context(dec_state.rnn_state.output())
      word_loss = translator.decoder.calc_loss(dec_state, ref_word)
      #import pdb;pdb.set_trace()
      la = dy.log_softmax(translator.decoder.get_scores(dec_state)).npvalue()
      tmp_err_rate=0
      if isinstance(word_loss.value(), list):
        lam=[x[0] for x in la]
        print(np.argmax(lam))
        print("-")
        print(ref_word[0])
        print(word_loss.value()[0])
        print("______")
        equal=(np.argmax(la,axis=0)==ref_word).sum()
        tmp_err_rate=(1-equal/la.shape[1])
        err_rate+=tmp_err_rate
        #import pdb;pdb.set_trace()
      #import pdb;pdb.set_trace()
      #equal=(np.argmax(la,axis=0)==ref_word).sum()
      #tmp_err_rate=(1-equal/la.shape[1])
      #err_rate+=tmp_err_rate
      if xnmt.batcher.is_batched(src) and trg_mask is not None:
        word_loss = trg_mask.cmult_by_timestep_expr(word_loss, i, inverse=True)
      losses.append(word_loss)
      if i < seq_len-1:
        dec_state = translator.decoder.add_input(dec_state, translator.trg_embedder.embed(ref_word))

    err_rate=err_rate/seq_len
    return dy.esum(losses), err_rate

class ReinforceLoss(Serializable):
  yaml_tag = '!ReinforceLoss'

  # TODO: document me

  def __init__(self, exp_global=Ref(Path("exp_global")), evaluation_metric=None, sample_length=50, use_baseline=False, decoder_hidden_dim=None):
    self.sample_length = sample_length
    if evaluation_metric is None:
      self.evaluation_metric = xnmt.evaluator.BLEUEvaluator(ngram=4, smooth=1)
    else:
      self.evaluation_metric = evaluation_metric
    self.use_baseline = use_baseline
    if self.use_baseline:
      model = exp_global.dynet_param_collection.param_col
      decoder_hidden_dim = decoder_hidden_dim or exp_global.default_layer_dim
      self.baseline = linear.Linear(input_dim=decoder_hidden_dim, output_dim=1, model=model)

  def __call__(self, translator, dec_state, src, trg):
    # TODO: apply trg.mask ?
    samples = []
    logsofts = []
    self.bs = []
    done = [False for _ in range(len(trg))]
    for _ in range(self.sample_length):
      dec_state.context = translator.attender.calc_context(dec_state.rnn_state.output())
      if self.use_baseline:
        h_t = dy.tanh(translator.decoder.context_projector(dy.concatenate([dec_state.rnn_state.output(), dec_state.context])))
        self.bs.append(self.baseline(dy.nobackprop(h_t)))
      logsoft = dy.log_softmax(translator.decoder.get_scores(dec_state))
      sample = logsoft.tensor_value().categorical_sample_log_prob().as_numpy()[0]
      # Keep track of previously sampled EOS
      sample = [sample_i if not done_i else Vocab.ES for sample_i, done_i in zip(sample, done)]
      # Appending and feeding in the decoder
      logsoft = dy.pick_batch(logsoft, sample)
      logsofts.append(logsoft)
      samples.append(sample)
      dec_state = translator.decoder.add_input(dec_state, translator.trg_embedder.embed(xnmt.batcher.mark_as_batch(sample)))
      # Check if we are done.
      if all([x == Vocab.ES for x in sample]):
        break

    samples = np.stack(samples, axis=1).tolist()
    self.eval_score = []
    for trg_i, sample_i in zip(trg, samples):
      # Removing EOS
      try:
        idx = sample_i.index(Vocab.ES)
        sample_i = sample_i[:idx]
      except ValueError:
        pass
      try:
        idx = trg_i.words.index(Vocab.ES)
        trg_i.words = trg_i.words[:idx]
      except ValueError:
        pass
      # Calculate the evaluation score
      score = 0 if not len(sample_i) else self.evaluation_metric.evaluate_fast(trg_i.words, sample_i)
      self.eval_score.append(score)
    self.true_score = dy.inputTensor(self.eval_score, batched=True)
    loss = LossBuilder()

    if self.use_baseline:
      for i, (score, _) in enumerate(zip(self.bs, logsofts)):
        logsofts[i] = dy.cmult(logsofts[i], score - self.true_score)
      loss.add_loss("Reinforce", dy.sum_elems(dy.esum(logsofts)))
    else:
      loss.add_loss("Reinforce", dy.sum_elems(dy.cmult(-self.true_score, dy.esum(logsofts))))

    if self.use_baseline:
      baseline_loss = []
      for bs in self.bs:
        baseline_loss.append(dy.squared_distance(self.true_score, bs))
      loss.add_loss("Baseline", dy.sum_elems(dy.esum(baseline_loss)))
    return loss

# To be implemented
class MinRiskLoss(Serializable):
  yaml_tag = 'MinRiskLoss'
