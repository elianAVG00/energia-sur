"""Exercise the additive territorial migration in a retained synthetic schema."""

import importlib
import os
import unittest
from uuid import uuid4

from alembic.migration import MigrationContext
from alembic.operations import Operations
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError


@unittest.skipUnless(os.environ.get("TEST_DATABASE_URL"), "Needs isolated PostgreSQL")
class TerritorialCatalogMigrationPostgresTest(unittest.TestCase):
    def test_upgrade_seed_rekey_and_downgrade(self) -> None:
        engine = create_engine(os.environ["TEST_DATABASE_URL"])
        schema = "territory_migration_" + uuid4().hex
        try:
            with engine.begin() as connection:
                connection.exec_driver_sql(f'CREATE SCHEMA "{schema}"')
                connection.exec_driver_sql(f'SET LOCAL search_path TO "{schema}"')
                connection.execute(text(
                    "CREATE TABLE es_outage_reports ("
                    "id text PRIMARY KEY, partido text NOT NULL, localidad text, "
                    "partido_key text NOT NULL, localidad_key text)"
                ))
                connection.execute(text(
                    "CREATE TABLE es_scheduled_works ("
                    "id text PRIMARY KEY, partido text NOT NULL, localidad text, "
                    "partido_key text NOT NULL, localidad_key text)"
                ))
                connection.execute(text(
                    "INSERT INTO es_outage_reports VALUES "
                    "('o1','Pte Perón','SAN JOSE','pte perón','san jose'),"
                    "('o2','CAÑUELAS',NULL,'cañuelas',NULL)"
                ))
                connection.execute(text(
                    "INSERT INTO es_scheduled_works VALUES "
                    "('w1','Cañuelas','Santa Anita','cañuelas','santa anita'),"
                    "('w2','LOMAS DE ZAMORA','Zona Rural','lomas de zamora','zona rural')"
                ))
                context = MigrationContext.configure(connection)
                with Operations.context(context):
                    migration = importlib.import_module(
                        "migrations.versions.0009_territorial_catalog",
                    )
                    migration.upgrade()
                    alias_party_migration = importlib.import_module(
                        "migrations.versions.0010_territorial_alias_party_fk",
                    )
                    alias_party_migration.upgrade()

                self.assertEqual(
                    connection.scalar(text(
                        "SELECT count(*) FROM es_territorial_parties",
                    )),
                    12,
                )
                self.assertEqual(
                    connection.scalar(text(
                        "SELECT count(*) FROM es_territorial_localities WHERE selectable",
                    )),
                    92,
                )
                self.assertEqual(
                    connection.scalar(text(
                        "SELECT count(*) FROM es_territorial_locality_sources",
                    )),
                    99,
                )
                self.assertEqual(
                    connection.scalar(text(
                        "SELECT count(*) FROM es_territorial_name_aliases "
                        "WHERE status='unresolved'",
                    )),
                    2,
                )
                self.assertEqual(
                    connection.execute(text(
                        "SELECT partido_key, localidad_key FROM es_outage_reports "
                        "WHERE id='o1'",
                    )).one(),
                    ("pte peron", "san jose"),
                )
                self.assertEqual(
                    connection.execute(text(
                        "SELECT partido, localidad FROM es_scheduled_works WHERE id='w1'",
                    )).one(),
                    ("Cañuelas", "Santa Anita"),
                )
                self.assertEqual(
                    connection.execute(text(
                        "SELECT partido_key, localidad_key FROM es_outage_reports "
                        "WHERE id='o2'",
                    )).one(),
                    ("canuelas", None),
                )
                self.assertEqual(
                    connection.execute(text(
                        "SELECT partido_key, localidad_key FROM es_scheduled_works "
                        "WHERE id='w2'",
                    )).one(),
                    ("lomas de zamora", "zona rural"),
                )
                self.assertEqual(
                    connection.execute(text(
                        "SELECT partido, localidad FROM es_scheduled_works WHERE id='w2'",
                    )).one(),
                    ("LOMAS DE ZAMORA", "Zona Rural"),
                )

                from app.territorial_catalog import seed_catalog

                seed_catalog(connection)
                self.assertEqual(
                    connection.scalar(text("SELECT count(*) FROM es_territorial_parties")),
                    12,
                )
                with self.assertRaises(IntegrityError), connection.begin_nested():
                    connection.execute(text(
                        "INSERT INTO es_territorial_parties "
                        "(georef_id,name,normalized_name) "
                        "VALUES ('02000','CAPITAL','capital')",
                    ))
                with self.assertRaises(IntegrityError), connection.begin_nested():
                    connection.execute(text(
                        "INSERT INTO es_territorial_localities "
                        "(id,party_georef_id,name,normalized_name) "
                        "VALUES ('duplicate','06028','San Jose','san jose')",
                    ))
                mismatched_locality = connection.scalar(text(
                    "SELECT id FROM es_territorial_localities "
                    "WHERE party_georef_id='06658' LIMIT 1",
                ))
                with self.assertRaises(IntegrityError), connection.begin_nested():
                    connection.execute(text(
                        "INSERT INTO es_territorial_name_aliases "
                        "(kind,source_label,normalized_source_key,party_georef_id,"
                        "locality_id,status,evidence) VALUES "
                        "('locality','WRONG PARTY','wrong party','06028',"
                        ":locality_id,'verified','synthetic test')",
                    ), {"locality_id": mismatched_locality})

                with Operations.context(context):
                    alias_party_migration.downgrade()
                    migration.downgrade()
                self.assertEqual(
                    connection.execute(text(
                        "SELECT partido_key, localidad_key FROM es_outage_reports "
                        "WHERE id='o1'",
                    )).one(),
                    ("pte perón", "san jose"),
                )
                self.assertEqual(
                    connection.execute(text(
                        "SELECT partido_key, localidad_key FROM es_scheduled_works "
                        "WHERE id='w1'",
                    )).one(),
                    ("cañuelas", "santa anita"),
                )
                self.assertEqual(
                    connection.execute(text(
                        "SELECT partido_key, localidad_key FROM es_outage_reports "
                        "WHERE id='o2'",
                    )).one(),
                    ("cañuelas", None),
                )
                self.assertEqual(
                    connection.execute(text(
                        "SELECT partido_key, localidad_key FROM es_scheduled_works "
                        "WHERE id='w2'",
                    )).one(),
                    ("lomas de zamora", "zona rural"),
                )
        finally:
            with engine.begin() as connection:
                connection.exec_driver_sql(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
            engine.dispose()
