CREATE OR REPLACE TABLE "aggregated_reviews" AS
SELECT
    "url",
    "publishedAtDate",
    "stars",
    "name",
    "text",
    'Google Places' AS "reviewSource"
FROM "apify_reviews"
WHERE "text" IS NOT NULL AND "text" <> '' AND "text" <> 'text'
LIMIT 500;