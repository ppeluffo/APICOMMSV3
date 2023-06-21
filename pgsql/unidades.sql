-- Table: public.configuraciones

-- DROP TABLE IF EXISTS public.tb_configuraciones;

CREATE TABLE IF NOT EXISTS public.configuraciones
(
    pk SERIAL PRIMARY KEY, 
    unit_id VARCHAR (20), 
    uid VARCHAR (50), 
    jconfig JSON
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.configuraciones
    OWNER to admin;
    