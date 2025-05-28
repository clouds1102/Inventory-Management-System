USE InventoryDB;
GO

-- 用户表
CREATE TABLE Users (
    user_id INT PRIMARY KEY IDENTITY(1,1),
    username NVARCHAR(50) NOT NULL UNIQUE,
    password NVARCHAR(100) NOT NULL,
    role NVARCHAR(20) NOT NULL,
    permission_level INT NOT NULL
);

-- 物料表
CREATE TABLE Material (
    material_id INT PRIMARY KEY IDENTITY(1,1),
    material_name NVARCHAR(100) NOT NULL,
    supplier NVARCHAR(100),
    unit NVARCHAR(20),
    max_quantity INT NOT NULL,
    min_quantity INT NOT NULL
);

-- 库存表
CREATE TABLE Inventory (
    inventory_id INT PRIMARY KEY IDENTITY(1,1),
    material_id INT NOT NULL,
    current_quantity INT NOT NULL,
    last_updated DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (material_id) REFERENCES Material(material_id)
);

-- 出入库记录表
CREATE TABLE InOutRecord (
    record_id INT PRIMARY KEY IDENTITY(1,1),
    material_id INT NOT NULL,
    user_id INT NOT NULL,
    type NVARCHAR(10) CHECK (type IN ('入库', '出库')),
    quantity INT NOT NULL,
    timestamp DATETIME DEFAULT GETDATE(),
    note NVARCHAR(255),
    FOREIGN KEY (material_id) REFERENCES Material(material_id),
    FOREIGN KEY (user_id) REFERENCES Users(user_id)
);

-- 盘点记录表
CREATE TABLE InventoryCheck (
    check_id INT PRIMARY KEY IDENTITY(1,1),
    material_id INT NOT NULL,
    real_quantity INT NOT NULL,
    recorded_quantity INT NOT NULL,
    adjusted_by_user INT NOT NULL,
    check_time DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (material_id) REFERENCES Material(material_id),
    FOREIGN KEY (adjusted_by_user) REFERENCES Users(user_id)
);

-- 库存预警表
CREATE TABLE Alert (
    alert_id INT PRIMARY KEY IDENTITY(1,1),
    material_id INT NOT NULL,
    alert_type NVARCHAR(20) CHECK (alert_type IN ('库存过低', '库存过高')),
    current_quantity INT NOT NULL,
    generated_time DATETIME DEFAULT GETDATE(),
    is_resolved BIT DEFAULT 0,
    FOREIGN KEY (material_id) REFERENCES Material(material_id)
);

-- 月结报表表
CREATE TABLE Report (
    report_id INT PRIMARY KEY IDENTITY(1,1),
    month NVARCHAR(7), -- 如 '2025-05'
    material_id INT NOT NULL,
    initial_quantity INT NOT NULL,
    in_quantity INT NOT NULL,
    out_quantity INT NOT NULL,
    final_quantity INT NOT NULL,
    generated_time DATETIME DEFAULT GETDATE(),
    FOREIGN KEY (material_id) REFERENCES Material(material_id)
);
