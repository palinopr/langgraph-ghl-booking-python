# Deployment Guide

## Prerequisites
- Node.js 20+
- Docker (optional)
- PM2 (optional)
- `.env` file with all required keys

## Deployment Options

### 1. Direct Node.js
```bash
npm install
npm run start:prod
```

### 2. PM2 (Recommended)
```bash
# Install PM2 globally
npm install -g pm2

# Start with PM2
npm run pm2:start

# View logs
npm run pm2:logs

# Monitor
npm run pm2:monitor

# Restart
npm run pm2:restart
```

### 3. Docker
```bash
# Build image
npm run docker:build

# Run container
npm run docker:run

# Or use docker-compose
npm run docker:compose
```

### 4. Cloud Platforms

#### Heroku
1. Create `Procfile`:
```
web: node index.js
```
2. Deploy via Git

#### AWS EC2
1. Use PM2 for process management
2. Set up Nginx reverse proxy
3. Configure SSL with Let's Encrypt

#### DigitalOcean App Platform
1. Connect GitHub repo
2. Set environment variables
3. Deploy automatically

## Environment Variables

Required:
- `OPENAI_API_KEY`
- `GHL_API_KEY`
- `GHL_LOCATION_ID`
- `GHL_CALENDAR_ID`

Optional:
- `LANGSMITH_API_KEY`
- `LANGSMITH_PROJECT`
- `PORT` (default: 3000)

## Production Checklist

- [ ] Set all environment variables
- [ ] Configure webhook URL in GHL
- [ ] Set up SSL certificate
- [ ] Configure domain/subdomain
- [ ] Set up monitoring (PM2/CloudWatch)
- [ ] Configure log rotation
- [ ] Set up backup strategy
- [ ] Test webhook connectivity

## Monitoring

### Health Check
```bash
curl http://localhost:3000/health
```

### PM2 Monitoring
```bash
pm2 status
pm2 logs
pm2 monit
```

### Docker Logs
```bash
docker logs outlet-media-bot
```

## Troubleshooting

1. **Bot not responding**: Check logs for errors
2. **Webhook failures**: Verify GHL webhook URL and SSL
3. **Memory issues**: Adjust PM2 memory limits
4. **API errors**: Check API keys and rate limits