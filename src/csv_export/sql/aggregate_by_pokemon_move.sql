SELECT
    pokemon,
    move1,
    move2,
    date(time) AS date,
    first_picked,
    first_picked_win,
    second_picked,
    second_picked_win,
    match_total
FROM "{db}"."{table}"
WHERE
    time = bin(now(), 1d) - 1d
    AND namespace = '{namespace}'
    AND measure_name = 'aggregate_by_pokemon_move'
ORDER BY first_picked + second_picked DESC
