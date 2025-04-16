# Stage 1: Build
FROM node:18-alpine AS builder
WORKDIR /app

# Copy package files and install dependencies
COPY package.json package-lock.json* ./
RUN npm install

ENV NEXT_PUBLIC_BACKEND_URL=#NEXT_PUBLIC_BACKEND_URL
ENV NEXT_PUBLIC_GOOGLE_ANALYTICS_ID=#NEXT_PUBLIC_GOOGLE_ANALYTICS_ID

# Copy project files and build the application
COPY . .
ENV NODE_ENV=production
ENV NEXT_TELEMETRY_DISABLED=1
RUN npm run build

# Stage 2: Production
FROM node:18-alpine
WORKDIR /app

# Copy only necessary files from the builder stage
COPY --from=builder /app/package.json ./
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/.next ./.next
COPY --from=builder /app/public ./public

# Expose port and define the command to run the application
ENV NEXT_TELEMETRY_DISABLED=1
EXPOSE 3000
CMD ["npm", "start"]
