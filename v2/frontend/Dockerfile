FROM node:18-alpine as build

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the app
COPY . .

# Build the app
RUN npm run build

# Production image
FROM nginx:alpine

# Copy built files to nginx
COPY --from=build /app/build /usr/share/nginx/html

# Copy nginx config if you have a custom one
# COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
