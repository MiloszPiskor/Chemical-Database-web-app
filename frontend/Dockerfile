# Multistep build for the Nginx container serving React Front

# Step 1: Build the React app using Node.js
FROM node:20 AS builder
WORKDIR /app
# Copy package.json and package-lock.json (leverage caching)
COPY Chemical-DB/package*.json ./
# Install dependencies
RUN npm install
# Copy the source files
COPY Chemical-DB/ ./
# Build the React app
RUN npm run build

# Step 2: Serve the React app with Nginx
FROM nginx:alpine AS runtime
# Remove default nginx index page
RUN rm -rf /usr/share/nginx/html/*
EXPOSE 80
# Copy the build folder from the builder step into the nginx html folder
COPY --from=builder /app/dist /usr/share/nginx/html
# handle React Router paths
COPY nginx.conf /etc/nginx/conf.d/default.conf
CMD ["nginx", "-g", "daemon off;"]
