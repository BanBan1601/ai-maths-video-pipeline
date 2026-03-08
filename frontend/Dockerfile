FROM --platform=linux/amd64 node:20-slim
WORKDIR /usr/src/app
COPY package.json package-lock.json* ./
RUN npm install
COPY . .
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"]
