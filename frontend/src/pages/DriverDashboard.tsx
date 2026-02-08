import { useState, useEffect } from 'react';
import { deliveriesApi } from '../api';
import { Delivery, DeliveryStatus } from '../types';
import toast from 'react-hot-toast';

export default function DriverDashboard() {
    const [deliveries, setDeliveries] = useState<Delivery[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchDeliveries();
    }, []);

    const fetchDeliveries = async () => {
        try {
            const response = await deliveriesApi.getMyDeliveries();
            if (response.success) {
                setDeliveries(response.data);
            }
        } catch (error) {
            toast.error('Failed to load deliveries');
        } finally {
            setLoading(false);
        }
    };

    const handleStatusUpdate = async (id: number, newStatus: DeliveryStatus) => {
        try {
            const response = await deliveriesApi.updateStatus(id, newStatus);
            if (response.success) {
                toast.success(`Delivery status updated to ${newStatus}`);
                setDeliveries(deliveries.map(d => d.id === id ? response.data : d));
            }
        } catch (error) {
            toast.error('Failed to update status');
        }
    };

    const getStatusColor = (status: DeliveryStatus) => {
        switch (status) {
            case 'assigned': return 'bg-yellow-100 text-yellow-800';
            case 'picked_up': return 'bg-blue-100 text-blue-800';
            case 'in_transit': return 'bg-purple-100 text-purple-800';
            case 'delivered': return 'bg-green-100 text-green-800';
            case 'failed': return 'bg-red-100 text-red-800';
            default: return 'bg-gray-100 text-gray-800';
        }
    };

    if (loading) {
        return <div className="p-8 text-center">Loading deliveries...</div>;
    }

    return (
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
            <h1 className="text-3xl font-bold mb-8">Driver Dashboard</h1>

            <div className="grid gap-6">
                {deliveries.length === 0 ? (
                    <p className="text-gray-500">No active deliveries assigned.</p>
                ) : (
                    deliveries.map((delivery) => (
                        <div key={delivery.id} className="bg-white p-6 rounded-lg shadow-md border hover:border-blue-500 transition-colors">
                            <div className="flex justify-between items-start mb-4">
                                <div>
                                    <h3 className="text-xl font-semibold">Order #{delivery.order_id}</h3>
                                    <p className="text-sm text-gray-500">Assigned: {new Date(delivery.created_at).toLocaleDateString()}</p>
                                </div>
                                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(delivery.status)} capitalize`}>
                                    {delivery.status.replace('_', ' ')}
                                </span>
                            </div>

                            <div className="space-y-2 mb-6">
                                {/* In a real app, we would join Order data to show address here */}
                                <p><span className="font-medium">Delivery Note:</span> {delivery.delivery_notes || 'None'}</p>
                                {delivery.current_location && <p><span className="font-medium">Current Location:</span> {delivery.current_location}</p>}
                            </div>

                            <div className="flex gap-3 border-t pt-4">
                                {delivery.status === 'assigned' && (
                                    <button
                                        onClick={() => handleStatusUpdate(delivery.id, 'picked_up')}
                                        className="flex-1 bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition"
                                    >
                                        Pick Up Order
                                    </button>
                                )}

                                {delivery.status === 'picked_up' && (
                                    <button
                                        onClick={() => handleStatusUpdate(delivery.id, 'in_transit')}
                                        className="flex-1 bg-purple-600 text-white px-4 py-2 rounded hover:bg-purple-700 transition"
                                    >
                                        Start Transit
                                    </button>
                                )}

                                {(delivery.status === 'in_transit' || delivery.status === 'picked_up') && (
                                    <button
                                        onClick={() => handleStatusUpdate(delivery.id, 'delivered')}
                                        className="flex-1 bg-green-600 text-white px-4 py-2 rounded hover:bg-green-700 transition"
                                    >
                                        Mark Delivered
                                    </button>
                                )}

                                {(delivery.status !== 'delivered' && delivery.status !== 'failed') && (
                                    <button
                                        onClick={() => handleStatusUpdate(delivery.id, 'failed')}
                                        className="px-4 py-2 text-red-600 hover:bg-red-50 rounded transition"
                                    >
                                        Report Issue
                                    </button>
                                )}
                            </div>
                        </div>
                    ))
                )}
            </div>
        </div>
    );
}
