import { pgTable, serial, timestamp, varchar, doublePrecision, bigint, index } from "drizzle-orm/pg-core"
import { sql } from "drizzle-orm"



export const healthCheck = pgTable("health_check", {
	id: serial().notNull(),
	updatedAt: timestamp("updated_at", { withTimezone: true, mode: 'string' }).defaultNow(),
});

export const industrySectors = pgTable("industry_sectors", {
	id: serial().notNull(),
	name: varchar("name", { length: 50 }).notNull().unique(),
	code: varchar("code", { length: 20 }).notNull().unique(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	updatedAt: timestamp("updated_at", { withTimezone: true, mode: 'string' }),
}, (table) => ({
	nameIdx: index("ix_industry_sectors_name").on(table.name),
	codeIdx: index("ix_industry_sectors_code").on(table.code),
}));

export const industryDailyData = pgTable("industry_daily_data", {
	id: bigint("id", { mode: "number" }).notNull(),
	sectorCode: varchar("sector_code", { length: 20 }).notNull(),
	tradeDate: varchar("trade_date", { length: 10 }).notNull(),
	openPrice: doublePrecision("open_price").notNull(),
	highPrice: doublePrecision("high_price").notNull(),
	lowPrice: doublePrecision("low_price").notNull(),
	closePrice: doublePrecision("close_price").notNull(),
	volume: bigint("volume", { mode: "number" }).notNull(),
	amount: doublePrecision("amount").notNull(),
	createdAt: timestamp("created_at", { withTimezone: true, mode: 'string' }).defaultNow().notNull(),
	updatedAt: timestamp("updated_at", { withTimezone: true, mode: 'string' }),
}, (table) => ({
	sectorCodeIdx: index("ix_industry_daily_data_sector_code").on(table.sectorCode),
	tradeDateIdx: index("ix_industry_daily_data_trade_date").on(table.tradeDate),
	sectorDateIdx: index("ix_industry_daily_data_sector_date").on(table.sectorCode, table.tradeDate),
}));
