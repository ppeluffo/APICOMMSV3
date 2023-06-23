-- Table: public.recoverid

-- DROP TABLE IF EXISTS public.recoverid;

CREATE TABLE IF NOT EXISTS public.recoverid
(
    uid VARCHAR (50) COLLATE pg_catalog."default" NOT NULL,
    id VARCHAR (30) COLLATE pg_catalog."default" NOT NULL,

    CONSTRAINT recoverid_pkey PRIMARY KEY (uid)
)

TABLESPACE pg_default;

ALTER TABLE IF EXISTS public.recoverid
    OWNER to admin;