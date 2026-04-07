#!/usr/bin/env bash
set -euo pipefail

CONTAINER_NAME="${CONTAINER_NAME:-shopping}"
HOSTNAME_VALUE="${HOSTNAME_VALUE:-localhost}"
PORT="${PORT:-7770}"
BASE_URL="http://${HOSTNAME_VALUE}:${PORT}"

echo "Configuring Magento base URL to ${BASE_URL}"

docker exec "$CONTAINER_NAME" /var/www/magento2/bin/magento setup:store-config:set --base-url="${BASE_URL}"
docker exec "$CONTAINER_NAME" mysql -u magentouser -pMyPassword magentodb -e \
  "UPDATE core_config_data SET value='${BASE_URL}/' WHERE path = 'web/secure/base_url';"
docker exec "$CONTAINER_NAME" /var/www/magento2/bin/magento cache:flush

for indexer in \
  catalogrule_product \
  catalogrule_rule \
  catalogsearch_fulltext \
  catalog_category_product \
  customer_grid \
  design_config_grid \
  inventory \
  catalog_product_category \
  catalog_product_attribute \
  catalog_product_price \
  cataloginventory_stock
do
  docker exec "$CONTAINER_NAME" /var/www/magento2/bin/magento indexer:set-mode schedule "$indexer"
done

echo "Shopping container configured."

