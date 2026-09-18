# ---- Étape 1 : build de l'app Angular ----
FROM node:20-alpine AS build
WORKDIR /app
COPY package*.json ./
# ngx-chess-board 2.2.3 cible Angular 13 → peer deps souples nécessaires
RUN npm install --legacy-peer-deps
COPY . .
RUN npm run build

# ---- Étape 2 : service des fichiers statiques via nginx ----
FROM nginx:1.27-alpine
COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist/frontend/browser /usr/share/nginx/html
EXPOSE 80
