--
-- PostgreSQL database dump
--

\restrict oCGj1YB216tO0Spoi3B5H51BL6TZH2bkaNLrNkUCqg15Op8R20VeEE7NTOu1CG6

-- Dumped from database version 18.6 (Postgres.app)
-- Dumped by pg_dump version 18.6 (Postgres.app)

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
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
-- Name: products; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.products (
    product_id bigint NOT NULL,
    product_name character varying(200) NOT NULL,
    category character varying(100) NOT NULL,
    original_price numeric(10,2) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT products_original_price_check CHECK ((original_price >= (0)::numeric))
);


--
-- Name: products_product_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.products ALTER COLUMN product_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.products_product_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: return_requests; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.return_requests (
    return_id bigint NOT NULL,
    customer_id bigint NOT NULL,
    product_id bigint NOT NULL,
    purchase_date date NOT NULL,
    return_reason text NOT NULL,
    item_condition character varying(30) NOT NULL,
    packaging_condition character varying(30) NOT NULL,
    functionality character varying(30) NOT NULL,
    status character varying(30) DEFAULT 'Submitted'::character varying NOT NULL,
    submitted_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT return_requests_functionality_check CHECK (((functionality)::text = ANY ((ARRAY['working'::character varying, 'partially_working'::character varying, 'not_working'::character varying, 'not_applicable'::character varying])::text[]))),
    CONSTRAINT return_requests_item_condition_check CHECK (((item_condition)::text = ANY ((ARRAY['new'::character varying, 'good'::character varying, 'damaged'::character varying, 'severely_damaged'::character varying])::text[]))),
    CONSTRAINT return_requests_packaging_condition_check CHECK (((packaging_condition)::text = ANY ((ARRAY['sealed'::character varying, 'opened'::character varying, 'damaged'::character varying, 'missing'::character varying])::text[]))),
    CONSTRAINT return_requests_status_check CHECK (((status)::text = ANY ((ARRAY['Submitted'::character varying, 'Pending Inspection'::character varying, 'Pending Approval'::character varying, 'Approved'::character varying, 'Processing'::character varying, 'Completed'::character varying, 'Cancelled'::character varying])::text[])))
);


--
-- Name: return_requests_return_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.return_requests ALTER COLUMN return_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.return_requests_return_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: return_status_history; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.return_status_history (
    history_id bigint NOT NULL,
    return_id bigint NOT NULL,
    changed_by bigint,
    old_status character varying(30),
    new_status character varying(30) NOT NULL,
    changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT new_status_valid CHECK (((new_status)::text = ANY ((ARRAY['Submitted'::character varying, 'Pending Inspection'::character varying, 'Pending Approval'::character varying, 'Approved'::character varying, 'Processing'::character varying, 'Completed'::character varying, 'Cancelled'::character varying])::text[]))),
    CONSTRAINT old_status_valid CHECK (((old_status IS NULL) OR ((old_status)::text = ANY ((ARRAY['Submitted'::character varying, 'Pending Inspection'::character varying, 'Pending Approval'::character varying, 'Approved'::character varying, 'Processing'::character varying, 'Completed'::character varying, 'Cancelled'::character varying])::text[])))),
    CONSTRAINT status_must_change CHECK (((old_status IS NULL) OR ((old_status)::text <> (new_status)::text)))
);


--
-- Name: return_status_history_history_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.return_status_history ALTER COLUMN history_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.return_status_history_history_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: routing_decisions; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.routing_decisions (
    decision_id bigint NOT NULL,
    return_id bigint NOT NULL,
    recommended_route character varying(20) NOT NULL,
    rule_applied character varying(100) NOT NULL,
    explanation text NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT routing_decisions_recommended_route_check CHECK (((recommended_route)::text = ANY ((ARRAY['Restock'::character varying, 'Refurbish'::character varying, 'Recycle'::character varying, 'Dispose'::character varying])::text[])))
);


--
-- Name: routing_decisions_decision_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.routing_decisions ALTER COLUMN decision_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.routing_decisions_decision_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: staff_reviews; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.staff_reviews (
    review_id bigint NOT NULL,
    return_id bigint NOT NULL,
    staff_id bigint NOT NULL,
    decision_id bigint NOT NULL,
    final_route character varying(20) NOT NULL,
    was_overridden boolean DEFAULT false NOT NULL,
    override_reason text,
    reviewed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT override_reason_required CHECK (((was_overridden = false) OR ((override_reason IS NOT NULL) AND (length(TRIM(BOTH FROM override_reason)) > 0)))),
    CONSTRAINT staff_reviews_final_route_check CHECK (((final_route)::text = ANY ((ARRAY['Restock'::character varying, 'Refurbish'::character varying, 'Recycle'::character varying, 'Dispose'::character varying])::text[])))
);


--
-- Name: staff_reviews_review_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.staff_reviews ALTER COLUMN review_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.staff_reviews_review_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: users; Type: TABLE; Schema: public; Owner: -
--

CREATE TABLE public.users (
    user_id bigint NOT NULL,
    full_name character varying(150) NOT NULL,
    email character varying(255) NOT NULL,
    password_hash text NOT NULL,
    role character varying(20) DEFAULT 'customer'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP NOT NULL,
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['customer'::character varying, 'staff'::character varying])::text[])))
);


--
-- Name: users_user_id_seq; Type: SEQUENCE; Schema: public; Owner: -
--

ALTER TABLE public.users ALTER COLUMN user_id ADD GENERATED ALWAYS AS IDENTITY (
    SEQUENCE NAME public.users_user_id_seq
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1
);


--
-- Name: products products_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.products
    ADD CONSTRAINT products_pkey PRIMARY KEY (product_id);


--
-- Name: return_requests return_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.return_requests
    ADD CONSTRAINT return_requests_pkey PRIMARY KEY (return_id);


--
-- Name: return_status_history return_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.return_status_history
    ADD CONSTRAINT return_status_history_pkey PRIMARY KEY (history_id);


--
-- Name: routing_decisions routing_decisions_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routing_decisions
    ADD CONSTRAINT routing_decisions_pkey PRIMARY KEY (decision_id);


--
-- Name: staff_reviews staff_reviews_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_reviews
    ADD CONSTRAINT staff_reviews_pkey PRIMARY KEY (review_id);


--
-- Name: users users_email_key; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_email_key UNIQUE (email);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (user_id);


--
-- Name: return_requests return_requests_customer_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.return_requests
    ADD CONSTRAINT return_requests_customer_id_fkey FOREIGN KEY (customer_id) REFERENCES public.users(user_id);


--
-- Name: return_requests return_requests_product_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.return_requests
    ADD CONSTRAINT return_requests_product_id_fkey FOREIGN KEY (product_id) REFERENCES public.products(product_id);


--
-- Name: return_status_history return_status_history_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.return_status_history
    ADD CONSTRAINT return_status_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(user_id);


--
-- Name: return_status_history return_status_history_return_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.return_status_history
    ADD CONSTRAINT return_status_history_return_id_fkey FOREIGN KEY (return_id) REFERENCES public.return_requests(return_id);


--
-- Name: routing_decisions routing_decisions_return_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.routing_decisions
    ADD CONSTRAINT routing_decisions_return_id_fkey FOREIGN KEY (return_id) REFERENCES public.return_requests(return_id);


--
-- Name: staff_reviews staff_reviews_decision_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_reviews
    ADD CONSTRAINT staff_reviews_decision_id_fkey FOREIGN KEY (decision_id) REFERENCES public.routing_decisions(decision_id);


--
-- Name: staff_reviews staff_reviews_return_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_reviews
    ADD CONSTRAINT staff_reviews_return_id_fkey FOREIGN KEY (return_id) REFERENCES public.return_requests(return_id);


--
-- Name: staff_reviews staff_reviews_staff_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: -
--

ALTER TABLE ONLY public.staff_reviews
    ADD CONSTRAINT staff_reviews_staff_id_fkey FOREIGN KEY (staff_id) REFERENCES public.users(user_id);


--
-- PostgreSQL database dump complete
--

\unrestrict oCGj1YB216tO0Spoi3B5H51BL6TZH2bkaNLrNkUCqg15Op8R20VeEE7NTOu1CG6

