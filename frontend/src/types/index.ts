import type { components } from './api'

export type User = components['schemas']['UserResponse']
export type UserCreate = components['schemas']['UserCreate']
export type UserUpdate = components['schemas']['UserUpdate']
export type UserRole = components['schemas']['UserRole']

export type AuthResponse = components['schemas']['AuthResponse']
export type TokenResponse = components['schemas']['TokenResponse']
export type LoginRequest = components['schemas']['LoginRequest']

export type Company = components['schemas']['CompanyResponse']
export type Customer = components['schemas']['CustomerResponse']

export type ServiceOrder = components['schemas']['ServiceOrderResponse']
export type ServiceOrderSummary = components['schemas']['ServiceOrderSummary']
export type ServiceItem = components['schemas']['ServiceItemResponse']
export type OrderStatus = components['schemas']['OrderStatus']
export type OrderPriority = components['schemas']['OrderPriority']

export type PaginatedUsers = components['schemas']['PaginatedResponse_UserResponse_']
export type PaginatedCustomers = components['schemas']['PaginatedResponse_CustomerResponse_']
export type PaginatedOrders = components['schemas']['PaginatedResponse_ServiceOrderSummary_']