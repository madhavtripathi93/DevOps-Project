# Use an official Node runtime as a parent image
FROM node:20-slim AS builder

# Set the working directory in the container
WORKDIR /app

# Install dependencies
COPY package*.json ./
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the production app
RUN npm run build

# Stage 2: Serve the app with a simple server
FROM node:20-slim

WORKDIR /app
RUN npm install -g serve
COPY --from=builder /app/dist ./dist

# Expose the port the app runs on
EXPOSE 5173

# Command to run the application
CMD ["serve", "-s", "dist", "-l", "5173"]
