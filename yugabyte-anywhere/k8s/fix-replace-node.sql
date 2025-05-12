DO $$
DECLARE
  tbl_name text := 'universe_replace_node_backup_' || to_char(now(), 'YYYYMMDD_HH24MISS');
BEGIN
  EXECUTE format('CREATE TABLE %I AS SELECT * FROM public.universe', tbl_name);
END
$$;

UPDATE public.universe
  set universe_details_json=
  (
    universe_details_json::jsonb
    || jsonb_build_object(
         'nodeDetailsSet',
         (
           SELECT jsonb_agg(
             CASE
               WHEN elem->>'state' = 'ToBeRemoved'
               THEN jsonb_set(elem, '{state}', to_jsonb('Live'::text))
               ELSE elem
             END
           )
           FROM jsonb_array_elements(universe_details_json::jsonb->'nodeDetailsSet') AS elem
           WHERE elem->>'state' IS DISTINCT FROM 'Adding'
         )
       )
    || jsonb_build_object('updatingTaskUUID', to_jsonb(null::text))
    || jsonb_build_object('updateSucceeded', to_jsonb(true))
    || jsonb_build_object('placementModificationTaskUuid', to_jsonb(null::text))
  )::jsonb::text;