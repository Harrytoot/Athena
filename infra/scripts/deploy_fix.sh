#!/bin/bash
cd /opt/athena
sed -i 's|from "./utils"|from "@/lib/utils"|' src/frontend/components/ui/MarketRegimeBadge.tsx
docker compose -f docker-compose.prod.yml --env-file .env.production build frontend
docker compose -f docker-compose.prod.yml --env-file .env.production up -d
