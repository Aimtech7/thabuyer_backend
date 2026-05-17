# 📋 API Contract Normalization Report - THA BUYER

## 🎯 Objective
Eliminate property naming inconsistencies between the Django backend (snake_case) and React frontend (camelCase) through a centralized mapping layer.

## 🛠️ Implementation: `mappers.ts`
Created a new service layer `services/django/mappers.ts` that provides robust, safe transformation functions for all core entities:

### 1. 👤 User Mapper
- **Source Fields**: `full_name`, `name`, `date_joined`, `is_active`, `verified`.
- **Target Fields**: `fullName`, `createdAt`, `isActive`, `isVerified`.
- **Logic**: Handles fallback for missing fields and ensures Boolean conversion for verification status.

### 2. 📦 Product Mapper
- **Source Fields**: `SKU`, `created_at`, `category_name`, `images`.
- **Target Fields**: `sku`, `createdAt`, `category`, `images`.
- **Logic**: Normalizes image arrays (extracting URLs from object structures) and flattens category objects.

### 3. 🛒 Cart & Order Mappers
- **Source Fields**: `total_amount`, `shipping_address`, `unit_price`, `product_name`.
- **Target Fields**: `totalAmount`, `deliveryAddress`, `price`, `productName`.
- **Logic**: Performs float parsing for monetary values to prevent precision issues on the frontend.

## 🚀 Integrated Services
The following services have been refactored to consume the new mapping layer:
- [x] **`auth.ts`**: Unified user profiles across login, registration, and session initialization.
- [x] **`orders.ts`**: Normalized order history and single order lookups.
- [x] **`products.ts`**: Standardized product listings and category objects.
- [x] **`cart.ts`**: Consistent item property names for state synchronization.
- [x] **`wishlist.ts`**: Ensured wishlisted items match standard product types.

## ✅ Result: TYPE SAFETY & CONSISTENCY
The frontend now consumes a **Normalized API Contract**. Developer friction caused by `createdAt` vs `created_at` is eliminated, and the codebase is significantly more maintainable.
