# Build stage
FROM node:24-alpine AS builder

WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy application code
COPY . .

# Build the application with static export
# The build process will use NEXT_PUBLIC_API_URL from build args
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL}

# Remove basePath for Docker deployment (only needed for GitHub Pages)
RUN sed -i '/basePath:/d' next.config.ts

RUN npm run build

# Production stage with nginx to serve static files
FROM nginx:alpine AS runner

WORKDIR /usr/share/nginx/html

# Remove default nginx static files
RUN rm -rf ./*

# Copy built static files from builder
COPY --from=builder /app/out .

# Copy custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -fsS http://127.0.0.1:80/health.html || exit 1

# Run nginx
CMD ["nginx", "-g", "daemon off;"]
