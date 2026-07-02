-- MarketFlow curated layer (Azure SQL Database)
CREATE SCHEMA curated;
GO
CREATE SCHEMA staging;
GO

CREATE TABLE staging.Trades
(
    trade_id      VARCHAR(64)     NOT NULL,
    [version]     INT             NOT NULL,
    symbol        VARCHAR(24)     NOT NULL,
    side          CHAR(4)         NOT NULL,
    quantity      DECIMAL(18, 4)  NOT NULL,
    price         DECIMAL(18, 6)  NOT NULL,
    notional      DECIMAL(28, 6)  NOT NULL,
    executed_at   DATETIME2(3)    NOT NULL,
    desk          VARCHAR(48)     NULL
);
GO

CREATE TABLE curated.Trades
(
    trade_id      VARCHAR(64)     NOT NULL PRIMARY KEY,
    [version]     INT             NOT NULL,
    symbol        VARCHAR(24)     NOT NULL,
    side          CHAR(4)         NOT NULL,
    quantity      DECIMAL(18, 4)  NOT NULL,
    price         DECIMAL(18, 6)  NOT NULL,
    notional      DECIMAL(28, 6)  NOT NULL,
    executed_at   DATETIME2(3)    NOT NULL,
    desk          VARCHAR(48)     NULL,
    updated_at    DATETIME2(3)    NOT NULL DEFAULT SYSUTCDATETIME()
);
GO

CREATE INDEX IX_curated_Trades_symbol_date
    ON curated.Trades (symbol, executed_at) INCLUDE (notional);
GO

CREATE TABLE curated.PipelineRunLog
(
    run_id        UNIQUEIDENTIFIER NOT NULL DEFAULT NEWID() PRIMARY KEY,
    job_name      VARCHAR(128)     NOT NULL,
    status        VARCHAR(16)      NOT NULL,
    attempt       INT              NOT NULL,
    started_at    DATETIME2(3)     NOT NULL,
    completed_at  DATETIME2(3)     NULL,
    error_message NVARCHAR(2048)   NULL
);
GO
