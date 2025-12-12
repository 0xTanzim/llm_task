-- Create customers table
CREATE TABLE customers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(20),
    city VARCHAR(50),
    country VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active'
);

-- Create orders table
CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    customer_id INTEGER NOT NULL REFERENCES customers(id) ON DELETE CASCADE,
    order_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_amount DECIMAL(10, 2),
    status VARCHAR(20) DEFAULT 'pending',
    shipping_address VARCHAR(255)
);

-- Create products table
CREATE TABLE products (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    category VARCHAR(50),
    price DECIMAL(10, 2),
    stock_quantity INTEGER,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create order_items table
CREATE TABLE order_items (
    id SERIAL PRIMARY KEY,
    order_id INTEGER NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    product_id INTEGER NOT NULL REFERENCES products(id),
    quantity INTEGER NOT NULL,
    unit_price DECIMAL(10, 2)
);

-- Insert fake customers
INSERT INTO customers (name, email, phone, city, country, status) VALUES
('John Doe', 'john.doe@example.com', '555-0101', 'New York', 'USA', 'active'),
('Jane Smith', 'jane.smith@example.com', '555-0102', 'Los Angeles', 'USA', 'active'),
('Bob Johnson', 'bob.johnson@example.com', '555-0103', 'Chicago', 'USA', 'inactive'),
('Alice Williams', 'alice.williams@example.com', '555-0104', 'Houston', 'USA', 'active'),
('Charlie Brown', 'charlie.brown@example.com', '555-0105', 'Phoenix', 'USA', 'active'),
('Diana Davis', 'diana.davis@example.com', '555-0106', 'Miami', 'USA', 'active'),
('Eve Miller', 'eve.miller@example.com', '555-0107', 'Seattle', 'USA', 'active'),
('Frank Wilson', 'frank.wilson@example.com', '555-0108', 'Boston', 'USA', 'inactive');

-- Insert fake products
INSERT INTO products (name, category, price, stock_quantity, description) VALUES
('Laptop Pro', 'Electronics', 1299.99, 50, 'High-performance laptop'),
('Wireless Mouse', 'Electronics', 29.99, 200, 'Ergonomic wireless mouse'),
('USB-C Cable', 'Accessories', 9.99, 500, '2-meter USB-C cable'),
('Monitor 4K', 'Electronics', 499.99, 30, '4K Ultra HD monitor'),
('Keyboard Mechanical', 'Electronics', 149.99, 75, 'RGB mechanical keyboard'),
('Phone Stand', 'Accessories', 19.99, 150, 'Adjustable phone stand'),
('Webcam HD', 'Electronics', 79.99, 100, '1080p HD webcam'),
('Desk Lamp', 'Lighting', 49.99, 80, 'LED desk lamp with USB');

-- Insert fake orders
INSERT INTO orders (customer_id, order_date, total_amount, status, shipping_address) VALUES
(1, '2024-01-15 10:30:00', 1329.98, 'delivered', '123 Main St, New York'),
(2, '2024-01-20 14:45:00', 549.98, 'shipped', '456 Oak Ave, Los Angeles'),
(3, '2024-02-01 09:15:00', 99.99, 'pending', '789 Elm St, Chicago'),
(1, '2024-02-10 16:20:00', 1799.97, 'processing', '123 Main St, New York'),
(4, '2024-02-15 11:00:00', 229.97, 'delivered', '321 Pine Rd, Houston'),
(5, '2024-02-20 13:30:00', 79.99, 'shipped', '654 Maple Dr, Phoenix'),
(6, '2024-02-25 10:45:00', 1429.95, 'pending', '987 Birch Ln, Miami'),
(7, '2024-03-01 15:00:00', 49.99, 'delivered', '147 Cedar Way, Seattle');

-- Insert fake order items
INSERT INTO order_items (order_id, product_id, quantity, unit_price) VALUES
(1, 1, 1, 1299.99),
(1, 2, 1, 29.99),
(2, 4, 1, 499.99),
(2, 5, 1, 49.99),
(3, 3, 10, 9.99),
(4, 1, 1, 1299.99),
(4, 6, 5, 19.99),
(5, 2, 1, 29.99),
(5, 3, 200, 1.99),
(6, 7, 1, 79.99),
(7, 4, 2, 499.99),
(7, 8, 2, 49.99),
(8, 5, 1, 149.99),
(8, 6, 1, 19.99);

-- Create indexes for better query performance
CREATE INDEX idx_customers_email ON customers(email);
CREATE INDEX idx_customers_city ON customers(city);
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status ON orders(status);
CREATE INDEX idx_order_items_order_id ON order_items(order_id);
CREATE INDEX idx_products_category ON products(category);
