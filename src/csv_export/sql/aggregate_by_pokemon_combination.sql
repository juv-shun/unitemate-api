SELECT
    pokemon,
    pokemon2,
    date(time) AS date,
    ally_win_total,
    ally_match_total,
    enemy_win_total,
    enemy_match_total
FROM "{db}"."{table}"
WHERE
    time = bin(now(), 1d) - 1d
    AND namespace = '{namespace}'
    AND measure_name = 'aggregate_by_pokemon_combination'
ORDER BY pokemon, pokemon2
