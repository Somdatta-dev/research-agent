FROM node:20-slim AS build

WORKDIR /app

RUN npm install -g pnpm@9

COPY package.json pnpm-lock.yaml* ./
RUN pnpm install --ignore-scripts --frozen-lockfile 2>/dev/null || pnpm install --ignore-scripts

COPY index.html tsconfig.json tsconfig.node.json vite.config.ts tailwind.config.ts postcss.config.js ./
COPY src/ src/
COPY scripts/ scripts/

RUN pnpm build

# --- Production image ---
FROM nginx:alpine

COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx/default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
