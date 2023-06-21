-- Table: public.configuraciones

-- DROP TABLE IF EXISTS public.tb_configuraciones;

CREATE TABLE IF NOT EXISTS public.usuarios
(
    user_id VARCHAR (30) COLLATE pg_catalog."default" NOT NULL, 
    fecha_ultimo_acceso timestamp(0) without time zone NOT NULL,
    data_ptr bigint,

    CONSTRAINT user_pkey PRIMARY KEY (user_id)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.usuarios
    OWNER to admin;
    