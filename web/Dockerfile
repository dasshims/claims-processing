FROM node:20-slim

WORKDIR /app

COPY package.json /app/package.json
RUN npm install

COPY . /app

RUN npm run build

EXPOSE 3000

CMD ["npm", "run", "start", "--", "--hostname", "0.0.0.0", "--port", "3000"]
