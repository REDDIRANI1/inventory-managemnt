import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import toast from 'react-hot-toast';
import { Plus, Trash2, Eye, X } from 'lucide-react';
import { ordersApi, customersApi, productsApi } from '../api/endpoints';
import Modal from '../components/Modal';

export default function Orders() {
  const queryClient = useQueryClient();
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isViewModalOpen, setIsViewModalOpen] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);
  
  // Order Form State
  const [selectedCustomer, setSelectedCustomer] = useState('');
  const [orderItems, setOrderItems] = useState([]);
  const [selectedProduct, setSelectedProduct] = useState('');
  const [quantity, setQuantity] = useState(1);

  const { data: orders, isLoading } = useQuery({ queryKey: ['orders'], queryFn: ordersApi.getAll });
  const { data: customers } = useQuery({ queryKey: ['customers'], queryFn: customersApi.getAll });
  const { data: products } = useQuery({ queryKey: ['products'], queryFn: productsApi.getAll });

  const createMutation = useMutation({
    mutationFn: ordersApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['products'] }); // Stock updated
      toast.success('Order created successfully');
      handleCloseModal();
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to create order');
    }
  });

  const deleteMutation = useMutation({
    mutationFn: ordersApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['orders'] });
      queryClient.invalidateQueries({ queryKey: ['products'] }); // Stock restored
      toast.success('Order deleted successfully');
    },
    onError: (error) => {
      toast.error(error.response?.data?.detail || 'Failed to delete order');
    }
  });

  const handleAddItem = () => {
    if (!selectedProduct || quantity < 1) return;
    
    const product = products.find(p => p.id === parseInt(selectedProduct));
    if (!product) return;

    if (quantity > product.quantity) {
      toast.error(`Only ${product.quantity} in stock for ${product.name}`);
      return;
    }

    const existingItemIndex = orderItems.findIndex(i => i.product_id === product.id);
    if (existingItemIndex >= 0) {
      const newItems = [...orderItems];
      const newQty = newItems[existingItemIndex].quantity + parseInt(quantity);
      if (newQty > product.quantity) {
        toast.error(`Cannot add more. Only ${product.quantity} in stock.`);
        return;
      }
      newItems[existingItemIndex].quantity = newQty;
      setOrderItems(newItems);
    } else {
      setOrderItems([...orderItems, { 
        product_id: product.id, 
        name: product.name,
        price: parseFloat(product.price),
        quantity: parseInt(quantity) 
      }]);
    }
    
    setSelectedProduct('');
    setQuantity(1);
  };

  const handleRemoveItem = (productId) => {
    setOrderItems(orderItems.filter(item => item.product_id !== productId));
  };

  const handleCreateOrder = () => {
    if (!selectedCustomer) {
      toast.error('Please select a customer');
      return;
    }
    if (orderItems.length === 0) {
      toast.error('Please add at least one item');
      return;
    }

    createMutation.mutate({
      customer_id: parseInt(selectedCustomer),
      items: orderItems.map(item => ({
        product_id: item.product_id,
        quantity: item.quantity
      }))
    });
  };

  const handleDelete = (id) => {
    if (window.confirm('Are you sure you want to delete this order?')) {
      deleteMutation.mutate(id);
    }
  };

  const handleCloseModal = () => {
    setIsModalOpen(false);
    setSelectedCustomer('');
    setOrderItems([]);
    setSelectedProduct('');
    setQuantity(1);
  };

  const currentTotal = orderItems.reduce((sum, item) => sum + (item.price * item.quantity), 0);

  return (
    <div>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-2xl font-semibold text-gray-900">Orders</h1>
        <button
          onClick={() => setIsModalOpen(true)}
          className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700"
        >
          <Plus className="h-4 w-4 mr-2" />
          Create Order
        </button>
      </div>

      <div className="bg-white shadow rounded-lg overflow-hidden">
        {isLoading ? (
          <div className="p-8 text-center text-gray-500">Loading orders...</div>
        ) : orders?.length === 0 ? (
          <div className="p-8 text-center text-gray-500">No orders found. Create one to get started.</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Order #</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Customer</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total</th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {orders?.map((order) => {
                  const cust = customers?.find(c => c.id === order.customer_id);
                  return (
                    <tr key={order.id}>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">#{order.id}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{cust?.full_name || `Customer ${order.customer_id}`}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{new Date(order.created_at).toLocaleDateString()}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${parseFloat(order.total_amount).toFixed(2)}</td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <button onClick={() => { setSelectedOrder(order); setIsViewModalOpen(true); }} className="text-indigo-600 hover:text-indigo-900 mr-4">
                          <Eye className="h-4 w-4" />
                        </button>
                        <button onClick={() => handleDelete(order.id)} className="text-red-600 hover:text-red-900">
                          <Trash2 className="h-4 w-4" />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Create Order Modal */}
      <Modal isOpen={isModalOpen} onClose={handleCloseModal} title="Create Order">
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700">Customer</label>
            <select 
              value={selectedCustomer} 
              onChange={(e) => setSelectedCustomer(e.target.value)}
              className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
            >
              <option value="">Select a customer...</option>
              {customers?.map(c => (
                <option key={c.id} value={c.id}>{c.full_name} ({c.email})</option>
              ))}
            </select>
          </div>

          <div className="pt-4 border-t border-gray-200">
            <h4 className="text-sm font-medium text-gray-900 mb-2">Add Items</h4>
            <div className="flex space-x-2">
              <select 
                value={selectedProduct} 
                onChange={(e) => setSelectedProduct(e.target.value)}
                className="flex-1 min-w-0 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
              >
                <option value="">Select product...</option>
                {products?.map(p => (
                  <option key={p.id} value={p.id} disabled={p.quantity === 0}>
                    {p.name} - ${parseFloat(p.price).toFixed(2)} ({p.quantity} in stock)
                  </option>
                ))}
              </select>
              <input 
                type="number" 
                min="1" 
                value={quantity} 
                onChange={(e) => setQuantity(e.target.value)}
                className="w-20 rounded-md border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-indigo-500 sm:text-sm border p-2"
              />
              <button 
                type="button" 
                onClick={handleAddItem}
                className="inline-flex items-center px-4 py-2 border border-indigo-600 text-sm font-medium rounded-md text-indigo-600 bg-white hover:bg-indigo-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <Plus className="h-4 w-4 mr-1.5" />
                Add
              </button>
            </div>
          </div>

          {orderItems.length > 0 && (
            <div className="mt-4">
              <h4 className="text-sm font-medium text-gray-900 mb-2">Order Summary</h4>
              <ul className="divide-y divide-gray-200 bg-gray-50 rounded-md border border-gray-200">
                {orderItems.map((item, idx) => (
                  <li key={idx} className="flex justify-between py-2 px-3 text-sm">
                    <span>{item.quantity}x {item.name}</span>
                    <div className="flex items-center">
                      <span className="font-medium mr-3">${(item.price * item.quantity).toFixed(2)}</span>
                      <button onClick={() => handleRemoveItem(item.product_id)} className="text-red-500 hover:text-red-700">
                        <X size={14} />
                      </button>
                    </div>
                  </li>
                ))}
                <li className="flex justify-between py-2 px-3 text-sm font-bold bg-gray-100 border-t border-gray-200">
                  <span>Total (Preview)</span>
                  <span>${currentTotal.toFixed(2)}</span>
                </li>
              </ul>
            </div>
          )}

          <div className="flex justify-end pt-4 mt-4 border-t border-gray-200">
            <button type="button" onClick={handleCloseModal} className="mr-3 px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50">Cancel</button>
            <button type="button" onClick={handleCreateOrder} disabled={createMutation.isLoading || orderItems.length === 0 || !selectedCustomer} className="px-4 py-2 text-sm font-medium text-white bg-indigo-600 border border-transparent rounded-md hover:bg-indigo-700 disabled:opacity-50">
              Submit Order
            </button>
          </div>
        </div>
      </Modal>

      {/* View Order Modal */}
      <Modal isOpen={isViewModalOpen} onClose={() => {setIsViewModalOpen(false); setSelectedOrder(null);}} title={`Order #${selectedOrder?.id}`}>
        {selectedOrder && (
          <div className="space-y-4">
            <div className="bg-gray-50 p-4 rounded-md border border-gray-200">
              <p className="text-sm text-gray-500">Date: <span className="text-gray-900 font-medium">{new Date(selectedOrder.created_at).toLocaleString()}</span></p>
              <p className="text-sm text-gray-500 mt-1">Customer ID: <span className="text-gray-900 font-medium">{selectedOrder.customer_id}</span></p>
            </div>
            
            <div>
              <h4 className="text-sm font-medium text-gray-900 mb-2">Items</h4>
              <ul className="divide-y divide-gray-200 border border-gray-200 rounded-md">
                {selectedOrder.items?.map((item) => {
                  const p = products?.find(p => p.id === item.product_id);
                  return (
                    <li key={item.id} className="py-2 px-3 text-sm flex justify-between bg-white">
                      <span>{item.quantity}x {p ? p.name : `Product #${item.product_id}`}</span>
                      <span className="font-medium">${(parseFloat(item.unit_price) * item.quantity).toFixed(2)}</span>
                    </li>
                  );
                })}
              </ul>
              <div className="flex justify-between mt-3 font-bold text-lg px-2">
                <span>Total Amount</span>
                <span>${parseFloat(selectedOrder.total_amount).toFixed(2)}</span>
              </div>
            </div>
          </div>
        )}
      </Modal>
    </div>
  );
}
