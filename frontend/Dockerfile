# ============================================================
# Clinical Intelligence Platform - Frontend (Next.js 14)
# ============================================================

# ---- Stage 1: Build ----
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json* ./
RUN npm ci --legacy-peer-deps

# BACKEND_URL is baked into the Next.js routes manifest at build time.
# Default points to the docker-compose service name "backend".
ARG BACKEND_URL=http://backend:5000
ENV BACKEND_URL=$BACKEND_URL

COPY . .
RUN npm run build

# ---- Stage 2: Production runner ----
FROM node:20-alpine AS runner

WORKDIR /app
ENV NODE_ENV=production

# Copy only what next start needs
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.mjs ./next.config.mjs

EXPOSE 3000

CMD ["npm", "start"]
