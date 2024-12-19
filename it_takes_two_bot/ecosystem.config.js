module.exports = {
  apps : [{
    name: 'it-takes-two-bot',
    cmd: 'bot.py',
    autorestart: false,
    watch: true,
    instances: 1,
    max_memory_restart: '1G',
    env: {
      ENV: 'development'
    },
    env_production : {
      ENV: 'production'
    }
  },
  ]
};
