--
-- PostgreSQL database dump
--

\restrict DdJ0avewLMyd62rNIIXKFSLLzSRyIESF10rusRcSNkm1anpqCQo9MP9O4QmtWkw

-- Dumped from database version 16.11
-- Dumped by pg_dump version 16.11

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: authors; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.authors (
    id integer NOT NULL,
    name character varying NOT NULL,
    bio character varying
);


ALTER TABLE public.authors OWNER TO "user";

--
-- Name: authors_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.authors_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.authors_id_seq OWNER TO "user";

--
-- Name: authors_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.authors_id_seq OWNED BY public.authors.id;


--
-- Name: book_authors; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.book_authors (
    book_id integer NOT NULL,
    author_id integer NOT NULL
);


ALTER TABLE public.book_authors OWNER TO "user";

--
-- Name: books; Type: TABLE; Schema: public; Owner: user
--

CREATE TABLE public.books (
    id integer NOT NULL,
    title character varying NOT NULL,
    description character varying
);


ALTER TABLE public.books OWNER TO "user";

--
-- Name: books_id_seq; Type: SEQUENCE; Schema: public; Owner: user
--

CREATE SEQUENCE public.books_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.books_id_seq OWNER TO "user";

--
-- Name: books_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: user
--

ALTER SEQUENCE public.books_id_seq OWNED BY public.books.id;


--
-- Name: authors id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.authors ALTER COLUMN id SET DEFAULT nextval('public.authors_id_seq'::regclass);


--
-- Name: books id; Type: DEFAULT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.books ALTER COLUMN id SET DEFAULT nextval('public.books_id_seq'::regclass);


--
-- Data for Name: authors; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.authors (id, name, bio) FROM stdin;
1	Isabel Allende	Novelista chilena.
2	Isabel Allende	Novelista chilena.
3	Jorge Luis Borges	Cuentista y ensayista argentino.
4	Laura Gallego	Autora española de fantasía juvenil.
5	Carlos Ruiz Zafón	Autor español, narrativa contemporánea.
\.


--
-- Data for Name: book_authors; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.book_authors (book_id, author_id) FROM stdin;
1	2
1	1
1	3
\.


--
-- Data for Name: books; Type: TABLE DATA; Schema: public; Owner: user
--

COPY public.books (id, title, description) FROM stdin;
1	La casa de los espíritus	Saga familiar con realismo mágico.
2	Cien años de soledad	Historia de Macondo y los Buendía.
3	Ficciones	Colección de relatos filosóficos y fantásticos.
4	Memorias de Idhún	Fantasía juvenil épica.
5	La sombra del viento	Misterio literario en la Barcelona de posguerra.
\.


--
-- Name: authors_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.authors_id_seq', 5, true);


--
-- Name: books_id_seq; Type: SEQUENCE SET; Schema: public; Owner: user
--

SELECT pg_catalog.setval('public.books_id_seq', 5, true);


--
-- Name: authors authors_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.authors
    ADD CONSTRAINT authors_pkey PRIMARY KEY (id);


--
-- Name: book_authors book_authors_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.book_authors
    ADD CONSTRAINT book_authors_pkey PRIMARY KEY (book_id, author_id);


--
-- Name: books books_pkey; Type: CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.books
    ADD CONSTRAINT books_pkey PRIMARY KEY (id);


--
-- Name: ix_authors_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_authors_id ON public.authors USING btree (id);


--
-- Name: ix_books_id; Type: INDEX; Schema: public; Owner: user
--

CREATE INDEX ix_books_id ON public.books USING btree (id);


--
-- Name: book_authors book_authors_author_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.book_authors
    ADD CONSTRAINT book_authors_author_id_fkey FOREIGN KEY (author_id) REFERENCES public.authors(id);


--
-- Name: book_authors book_authors_book_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: user
--

ALTER TABLE ONLY public.book_authors
    ADD CONSTRAINT book_authors_book_id_fkey FOREIGN KEY (book_id) REFERENCES public.books(id);


--
-- PostgreSQL database dump complete
--

\unrestrict DdJ0avewLMyd62rNIIXKFSLLzSRyIESF10rusRcSNkm1anpqCQo9MP9O4QmtWkw

