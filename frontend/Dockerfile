FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json ./

# Install dependencies (use npm install to handle missing package-lock.json)
RUN npm install

# Copy application code
COPY . .

# Build the application
ENV NEXT_PUBLIC_API_URL=http://localhost:8000
RUN npm run build

# Expose port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]

