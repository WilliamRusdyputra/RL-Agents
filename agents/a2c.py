import tensorflow as tf
from threading import Thread
from .agent_utils import build_actor, build_critic


class A2CAgent:
    def __init__(self, env):
        self.path = ['./weights_a2c/actor/actor', './weights_a2c/critic/critic']
        self.env = env
        self.state_shape = env.observation_space.shape
        self.action_space = env.action_space.n
        self.n_agent = 4
        self.global_actor = build_actor(self.action_space, self.state_shape)
        self.global_critic = build_critic(self.state_shape)
        self.max_steps = 2e2
        self.max_loop = 1e4
        self.discount = 0.95

    def choose_action(self, observation):
        return self.global_actor.predict(observation)

    def create_workers(self):
        workers = []
        for i in range(self.n_agent):
            worker_actor = build_actor(self.action_space, self.state_shape)
            worker_critic = build_critic(self.state_shape)
            workers.append([worker_actor, worker_critic])
        return workers

    def train(self, actor, critic):
        actor.set_weights(self.global_actor.get_weights())
        critic.set_weights(self.global_critic.get_weights())

        step = 0
        while step < self.max_loop:
            observation = self.env.reset()
            terminated = False

            observations = [observation]
            rewards = []
            actions = []
            time_step = 1

            while not terminated and time_step < self.max_steps:
                action = actor.predict(observation)

                observation, reward, terminated, _ = self.env.step(action)

                observations.append(observation)
                rewards.append(reward)
                actions.append(action)
                time_step += 1

            if terminated:
                return_estimation = 0
            else:
                return_estimation = critic.predict(observation)

            actor_gradients = None
            critic_gradients = None
            for i in range(len(observations)):
                return_estimation = self.discount * return_estimation + rewards[i]
                td_error = return_estimation - critic.predict(observation[i])
                actor_target = tf.concat([actions[i], td_error], axis=1)
                with tf.GradientTape() as tape:
                    actor_loss = actor.loss(actor_target, actor.predict(observations[i]))
                    critic_loss = critic.loss(td_error, critic.predict(observations[i]))

                # accumulate gradients w.r.t parameters
                actor_gradient = tape.gradient(actor_loss, actor.trainable_weights)
                if actor_gradients is None:
                    actor_gradients = actor_gradient
                else:
                    actor_gradients += actor_gradient

                critic_gradient = tape.gradient(critic_loss, critic.trainable_weights)
                if critic_gradients is None:
                    critic_gradients = critic_gradient
                else:
                    critic_gradients += critic_gradient

            optimizer = self.global_actor.optimizer
            optimizer.apply_gradients(zip(actor_gradients, self.global_actor.trainable_weights))
            optimizer = self.global_critic.optimizer
            optimizer.apply_gradients(zip(critic_gradients, self.global_critic.trainable_weights))
            step += 1

    def assign_workers(self):
        workers = self.create_workers()