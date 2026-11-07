FROM node:24.22.2-bookworm-slim@sha256:01d566e8d94d8c619591d78652babfccd3c6992a3dffa9ed5ab39e11cf6c70e9 AS runtime

WORKDIR /app

COPY package*.json .npmrc ./
RUN test "$(node --version)" = "v24.22.2" \
    && test "$(npm --version)" = "11.19.1" \
    && npm ci

COPY index.html tsconfig.json vite.config.ts playwright.config.ts components.json ./
COPY src ./src
COPY tests ./tests
COPY e2e ./e2e
RUN npm run build && npm test && npm run lint && chown -R node:node /app

USER node
EXPOSE 5173
CMD ["npm", "run", "dev"]

FROM runtime AS verification
USER root
ENV PLAYWRIGHT_BROWSERS_PATH=/opt/playwright
RUN npx playwright install --with-deps --only-shell chromium
USER node

FROM runtime AS development
