-- Idempotent MERGE from staging into curated (invoked by MF_LOAD_CURATED)
CREATE OR ALTER PROCEDURE curated.usp_MergeTrades
AS
BEGIN
    SET NOCOUNT ON;
    SET XACT_ABORT ON;

    BEGIN TRANSACTION;

    MERGE curated.Trades AS tgt
    USING (
        SELECT trade_id, [version], symbol, side, quantity, price,
               notional, executed_at, desk,
               ROW_NUMBER() OVER (PARTITION BY trade_id ORDER BY [version] DESC) AS rn
        FROM staging.Trades
    ) AS src
        ON tgt.trade_id = src.trade_id
    WHEN MATCHED AND src.rn = 1 AND src.[version] > tgt.[version] THEN
        UPDATE SET [version]   = src.[version],
                   symbol      = src.symbol,
                   side        = src.side,
                   quantity    = src.quantity,
                   price       = src.price,
                   notional    = src.notional,
                   executed_at = src.executed_at,
                   desk        = src.desk,
                   updated_at  = SYSUTCDATETIME()
    WHEN NOT MATCHED BY TARGET AND src.rn = 1 THEN
        INSERT (trade_id, [version], symbol, side, quantity, price, notional, executed_at, desk)
        VALUES (src.trade_id, src.[version], src.symbol, src.side, src.quantity,
                src.price, src.notional, src.executed_at, src.desk);

    TRUNCATE TABLE staging.Trades;

    COMMIT TRANSACTION;
END
GO

-- Daily P&L-style rollup consumed by reporting
CREATE OR ALTER PROCEDURE curated.usp_GetDailySummary
    @TradeDate DATE
AS
BEGIN
    SET NOCOUNT ON;

    SELECT symbol,
           desk,
           side,
           COUNT(*)        AS trade_count,
           SUM(quantity)   AS total_quantity,
           SUM(notional)   AS total_notional,
           AVG(price)      AS avg_price
    FROM curated.Trades
    WHERE CAST(executed_at AS DATE) = @TradeDate
    GROUP BY symbol, desk, side
    ORDER BY total_notional DESC;
END
GO
