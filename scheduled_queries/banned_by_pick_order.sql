WITH valid_matches AS (
    SELECT match_id, max_by(winner, cnt) AS winner
    FROM (
        SELECT match_id, winner, COUNT(*) AS cnt
        FROM "unitemate-api-prd"."origin_user_results-prd"
        WHERE time BETWEEN bin(@scheduled_runtime, 1d) - 1d AND bin(@scheduled_runtime, 1d)
            AND namespace = 'default'
        GROUP BY match_id, winner
        HAVING COUNT(*) >= 5
    )
    GROUP BY match_id
    HAVING max_by(winner, cnt) <> 'invalid'
), filter_by_valid_matches AS (
    SELECT
        valid_matches.match_id,
        valid_matches.winner,
        is_first_pick,
        time,
        pokemon,
        move1,
        move2,
        banned_pokemon_0,
        rate
    FROM "unitemate-api-prd"."origin_user_results-prd" AS origin
    JOIN valid_matches ON origin.match_id = valid_matches.match_id
)

SELECT
    pokemon,
    IF(is_first_pick, '先攻', '後攻') AS pick_order,
    bin(@scheduled_runtime, 1d) - 1d AS time,
    'aggregate_banned_pokemon' AS measure_name,
    COUNT(DISTINCT match_id) AS banned
FROM (
    SELECT match_id, is_first_pick, max_by(pokemon, banned) AS pokemon
    FROM (
        SELECT match_id, is_first_pick, banned_pokemon_0 as pokemon, COUNT(*) AS banned
        FROM filter_by_valid_matches
        GROUP BY match_id, is_first_pick, banned_pokemon_0
    )
    GROUP BY match_id, is_first_pick
) AS banned_pokemons
GROUP BY is_first_pick, pokemon
ORDER BY is_first_pick, banned DESC
