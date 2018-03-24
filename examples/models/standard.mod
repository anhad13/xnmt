!Experiment
evaluate:
- !AccuracyEvalTask
  eval_metrics: bleu
  hyp_file: examples/output/{EXP}.test_hyp
  model: !Ref {path: model}
  ref_file: examples/data/head.ja
  src_file: examples/data/head.en
exp_global: !ExpGlobal
  bias_init: !ZeroInitializer {}
  commandline_args: !!python/object:argparse.Namespace
    dynet_autobatch: null
    dynet_devices: null
    dynet_gpu: false
    dynet_gpu_ids: null
    dynet_gpus: null
    dynet_mem: null
    dynet_profiling: null
    dynet_seed: null
    dynet_viz: false
    dynet_weight_decay: null
    experiment_name: []
    experiments_file: examples/01_standard.yaml
    generate_doc: false
    settings: settings.standard
  default_layer_dim: 512
  dropout: 0.3
  log_file: '{EXP_DIR}/logs/{EXP}.log'
  model_file: '{EXP_DIR}/models/{EXP}.mod'
  param_init: !GlorotInitializer {}
model: !TreeTranslator
  attender: !MlpAttender
    exp_global: !Ref {path: exp_global}
    hidden_dim: 512
    input_dim: 512
    state_dim: 512
  decoder: !MlpSoftmaxDecoder
    bridge: !CopyBridge
      dec_dim: 512
      dec_layers: 1
      exp_global: !Ref {path: exp_global}
    exp_global: !Ref {path: exp_global}
    input_dim: 512
    layers: 1
    lstm_dim: 512
    mlp_hidden_dim: 512
    trg_embed_dim: 512
    trg_reader: !Ref {path: model.trg_reader}
  encoder: !TreeLSTMSeqTransducer
    exp_global: !Ref {path: exp_global}
    hidden_dim: 512
    layers: 1
  inference: !SimpleInference
    batcher: !SrcBatcher {batch_size: 32}
  src_embedder: !SimpleWordEmbedder
    exp_global: !Ref {path: exp_global}
    src_reader: !Ref {path: model.src_reader}
    trg_reader: !Ref {path: model.trg_reader}
  src_reader: !TreeTextReader
    vocab: !Vocab
      i2w: [<s>, </s>, ., you, '?', a, do, the, in, it, to, with, for, is, minutes,
        time, tiger, case, person, what, mail, his, through, will, this, at, leave,
        'no', from, question, smile, stared, wait, '&apos;s', principal, he, judge,
        there, interesting, looks, e, determining, by, when, where, matter, escaped,
        one, '&apos;t', afternoon, get, zoo, an, element, regarding, has, thank, your,
        shouldn, satirical, day, work, five, want, me, please, '@-@', can, <unk>]
      vocab_file: null
  trg_embedder: !SimpleWordEmbedder
    emb_dim: 512
    exp_global: !Ref {path: exp_global}
    src_reader: !Ref {path: model.src_reader}
    trg_reader: !Ref {path: model.trg_reader}
  trg_reader: !PlainTextReader
    vocab: !Vocab
      i2w: [<s>, </s>, "\u3002", "\u3044", "\u3067", "\u3092", "\u304C", "\u306F",
        "\u305F", "\u306A", "\u3057", "\u3059", "\u306E", "\u3066", "\u308B", "\u304B",
        "\u4E00", "\u304D", "\u4EF6", "\u79C1", "\u307E", "\u304B\u3089", "\u7B11\u3044",
        "\u4F55", "\u3067\u304D", "\u5F85", "\u6642\u9593", "\u305F\u3061", "\u4E3B\u8981",
        "\u30C8\u30E9", "\u3061", "\u7D42\u308F", "\u3042\u306A\u305F", "\u982D",
        "\u8131\u8D70", "\u541B", "\u76AE\u8089", "\u304F\u3060\u3055", "\u6C7A\u5B9A",
        "\u65E5", "\u30E1\u30FC\u30EB", "\u8981\u7D20", "\u5348\u5F8C", "\u3044\u305F\
          \u3060", "\u3053\u308C", "\u52D5\u7269", "\u5206", "\u5DEE\u3057\u8FEB",
        "\u3079", "\u4E88\u5B9A", "\u5B58\u5728", "\u3063", "\u3044\u3064", "\u5712",
        "\u5F7C", "\u3042\u308A\u304C\u3068\u3046", "\u4EBA", "\u4ED5\u4E8B", "\u3054\u3056",
        "\u51FA\u767A", "\u5224\u65AD", "\u898B\u3064\u3081", "\u4F8B", "\u6D6E\u304B\
          \u3079", "\u3042", "\u5916\u898B", "\u305D\u308C", "\u6DF1", "\u8208\u5473",
        "\u304A", "\uFF15", "\uFF11", <unk>]
      vocab_file: null
train: !SimpleTrainingRegimen
  batcher: !Ref {path: model.inference.batcher}
  dev_tasks:
  - !LossEvalTask
    batcher: !Ref {path: model.inference.batcher}
    model: !Ref {path: model}
    ref_file: examples/data/head.ja
    src_file: examples/data/head.en
  exp_global: !Ref {path: exp_global}
  model: !Ref {path: model}
  run_for_epochs: 2
  src_file: examples/data/head.en
  trainer: !AdamTrainer
    alpha: 0.001
    exp_global: !Ref {path: exp_global}
  trg_file: examples/data/head.ja
