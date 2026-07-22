# ==========================================
# BASE STAGE
# ==========================================
FROM node:20-alpine AS base

WORKDIR /app

# Copy dependency configs
COPY package.json package-lock.json ./

# Install packages
RUN npm install

# ==========================================
# DEVELOPMENT STAGE
# ==========================================
FROM base AS development

COPY . .

EXPOSE 3000

ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["npm", "run", "dev"]

# ==========================================
# BUILDER STAGE
# ==========================================
FROM base AS builder

COPY . .

# Run build
RUN npm run build

# ==========================================
# PRODUCTION RUNNER STAGE
# ==========================================
FROM node:20-alpine AS production

WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

# Copy package and lock files
COPY package.json package-lock.json ./
RUN npm install --omit=dev

# Copy built app and config files
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public
COPY --from=builder /app/next.config.ts ./
COPY --from=builder /app/tsconfig.json ./

EXPOSE 3000

CMD ["npm", "run", "start"]

