import gym
import torch
from agents.ppo import PPOAgent
from agents.agent_utils import Memory

device = torch.device('cuda:0' if torch.cuda.is_available() else 'cpu')

max_episode = 1e4
max_steps = 2e3

UPDATE_STEP = 2e3

env = gym.make("BipedalWalker-v3")

memory = Memory()
agent = PPOAgent(env)

total_reward = 0
time_step = 0

for i in range(1, int(max_episode)):
    observation = env.reset()
    total_reward = 0
    episode_step = 0
    for _ in range(int(max_steps)):
        env.render()

        action = agent.choose_action(observation, memory)
        observation, reward, terminated, _ = env.step(action)

        time_step += 1
        episode_step += 1
        total_reward += reward

        memory.rewards.append(reward)
        memory.terminals.append(terminated)

        if time_step % UPDATE_STEP == 0:
            agent.update(memory)
            memory.reset()
            time_step = 0
            print('AGENT UPDATED')
        
        if terminated:
            print('EPISODE {} COMPLETED WITH REWARD: {} STEP: {}'.format(i, total_reward, episode_step))
            episode_step = 0
            break

    if i % 100 == 0:
        torch.save(agent.policy.state_dict(), agent.path)
