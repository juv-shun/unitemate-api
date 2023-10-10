WITH t1 AS (
	SELECT namespace, match_id, pick_order, pokemon, result
	FROM "unitemate-api-prd"."processed-origin-prd"
    WHERE
        time between bin(now(), 1d) - 2d AND bin(now(), 1d)
        AND measure_name = 'user_result'
), allies AS (
	SELECT t1.namespace, t1.match_id, t1.pokemon, t2.pokemon AS pokemon2, t1.result
	FROM t1
	JOIN t1 AS t2 ON t1.namespace = t2.namespace AND t1.match_id = t2.match_id AND t1.pick_order = t2.pick_order
	WHERE t1.pokemon != t2.pokemon
), enemies AS (
	SELECT t1.namespace, t1.match_id, t1.pokemon, t2.pokemon AS pokemon2, t1.result
	FROM t1
	JOIN t1 AS t2 ON t1.namespace = t2.namespace AND t1.match_id = t2.match_id AND t1.pick_order != t2.pick_order
)

SELECT
    namespace,
    pokemon,
    pokemon2,
    bin(now(), 1d) - 1d AS time,
    'aggregate_ally_pokemon' AS measure_name,
    result,
    COUNT(DISTINCT match_id) AS match_total
FROM allies
GROUP BY namespace, pokemon, pokemon2, result
UNION ALL
SELECT
    namespace,
    pokemon,
    pokemon2,
    bin(now(), 1d) - 1d AS time,
    'aggregate_enemy_pokemon' AS measure_name,
    result,
    COUNT(DISTINCT match_id) AS match_total
FROM enemies
GROUP BY namespace, pokemon, pokemon2, result
ORDER BY namespace, pokemon, pokemon2, match_total DESC
