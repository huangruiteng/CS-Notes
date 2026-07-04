from keras import backend as K
from keras.optimizers import Optimizer, SGD


# Ported from https://github.com/NVIDIA/OpenSeq2Seq/blob/master/open_seq2seq/optimizers/novograd.py
class NovoGrad(Optimizer):
    """NovoGrad optimizer.
    Default parameters follow those provided in the original paper.
    # Arguments
        lr: float >= 0. Learning rate.
        final_lr: float >= 0. Final learning rate.
        beta_1: float, 0 < beta < 1. Generally close to 1.
        beta_2: float, 0 < beta < 1. Generally close to 1.
        gamma: float >= 0. Convergence speed of the bound function.
        epsilon: float >= 0. Fuzz factor. If `None`, defaults to `K.epsilon()`.
        decay: float >= 0. Learning rate decay over each update.
        weight_decay: Weight decay weight.
        amsgrad: boolean. Whether to apply the AMSBound variant of this
            algorithm.
    # References
        - [Stochastic Gradient Methods with Layer-wise Adaptive Moments for Training of Deep Networks]
          (https://arxiv.org/abs/1905.11286)
        - [Adam - A Method for Stochastic Optimization]
          (https://arxiv.org/abs/1412.6980v8)
    """

    def __init__(self, lr=0.01, beta_1=0.95, beta_2=0.98,
                 epsilon=None, decay=0., weight_decay=0.0,
                 amsgrad=False, grad_averaging=False, **kwargs):
        super(NovoGrad, self).__init__(**kwargs)

        with K.name_scope(self.__class__.__name__):
            self.iterations = K.variable(0, dtype='int64', name='iterations')
            self.lr = K.variable(lr, name='lr')
            self.beta_1 = K.variable(beta_1, name='beta_1')
            self.beta_2 = K.variable(beta_2, name='beta_2')
            self.decay = K.variable(decay, name='decay')

        if epsilon is None:
            epsilon = 1e-8
        self.epsilon = epsilon
        self.initial_decay = decay
        self.amsgrad = amsgrad
        self.grad_averaging = grad_averaging

        self.weight_decay = float(weight_decay)

    def get_updates(self, loss, params):
        grads = self.get_gradients(loss, params)
        self.updates = [K.update_add(self.iterations, 1)]

        lr = self.lr
        if self.initial_decay > 0:
            lr = lr * (1. / (1. + self.decay * K.cast(self.iterations,
                                                      K.dtype(self.decay))))
        # momentum
        moments = [K.zeros(K.int_shape(p), dtype=K.dtype(p)) for p in params]
        grads_ema = [K.zeros([], dtype=K.floatx()) for _ in params]  # v^l_t

        if self.amsgrad:
            vhats = [K.zeros([], dtype=K.floatx()) for _ in grads_ema]
        else:
            vhats = [K.zeros([]) for _ in grads_ema]

        self.weights = [self.iterations] + moments + grads_ema + vhats

        for p, g, m, g_ema, vhat in zip(params, grads, moments, grads_ema, vhats):
            # compute ema for grads^2 for each layer
            g_2 = K.sum(K.square(x=K.cast(g, K.floatx())))
            g_ema_new = K.switch(K.equal(g_ema, 0.),
                                 g_2,
                                 g_ema * self.beta_2 + g_2 * (1.0 - self.beta_2))

            if self.amsgrad:
                g_ema_new = K.maximum(vhat, g_ema_new)
                self.updates.append(K.update(vhat, g_ema_new))

            g *= 1.0 / (K.sqrt(g_ema_new) + self.epsilon)

            # weight decay
            if self.weight_decay > 0.0:
                g += (self.weight_decay * p)

            # Momentum --> SAG
            if self.grad_averaging:
                g *= (1.0 - self.beta_1)

            m_t = self.beta_1 * m + g  # velocity

            self.updates.append(K.update(m, m_t))
            self.updates.append(K.update(g_ema, g_ema_new))

            new_p = p - lr * m_t

            # Apply constraints.
            if getattr(p, 'constraint', None) is not None:
                new_p = p.constraint(new_p)

            self.updates.append(K.update(p, new_p))
        return self.updates

    def get_config(self):
        config = {'lr': float(K.get_value(self.lr)),
                  'beta_1': float(K.get_value(self.beta_1)),
                  'beta_2': float(K.get_value(self.beta_2)),
                  'decay': float(K.get_value(self.decay)),
                  'epsilon': self.epsilon,
                  'weight_decay': self.weight_decay,
                  'grad_averaging': self.grad_averaging,
                  'amsgrad': self.amsgrad}
        base_config = super(NovoGrad, self).get_config()
        return dict(list(base_config.items()) + list(config.items()))