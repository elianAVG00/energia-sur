FROM node:24.22.2-bookworm-slim@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9

WORKDIR /app

COPY package*.json .npmrc ./
RUN test "$(node --version)" = "v24.22.2" \
    && test "$(npm --version)" = "11.19.1" \
    && npm ci

COPY index.html tsconfig.json vite.config.ts ./
COPY src ./src
COPY tests ./tests
RUN npm run build && npm test && chown -R node:node /app

USER node
EXPOSE 5173
CMD ["npm", "run", "dev"]
