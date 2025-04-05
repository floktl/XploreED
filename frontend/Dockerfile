FROM node:18

WORKDIR /app

COPY package*.json ./
RUN npm install

COPY . .

# Tailwind + Vite dev server in parallel
CMD ["sh", "-c", "npm run watch:css & npm run dev -- --host"]
