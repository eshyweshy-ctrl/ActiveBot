# ACTIVEBOT - Frontend Dockerfile
FROM node:20-alpine AS build

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies and fix ajv issue
RUN npm install --legacy-peer-deps && npm install ajv@8 ajv-keywords@5 --save-dev --legacy-peer-deps

# Copy source code
COPY . .

# Build argument for backend URL
ARG REACT_APP_BACKEND_URL
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL

# Build the app
RUN npm run build

# Production stage with nginx
FROM nginx:alpine

# Copy built assets
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
