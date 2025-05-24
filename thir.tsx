import React, { useState } from 'react';
import { Card, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import { Bell, MessageCircle, Home, Plus } from 'lucide-react';

export default function SellersDashboard() {
  const [listings, setListings] = useState([]);
  const [form, setForm] = useState({
    title: '',
    address: '',
    price: '',
    description: ''
  });

  const handleInputChange = (e) => {
    const { name, value } = e.target;
    setForm({ ...form, [name]: value });
  };

  const handleCreateListing = () => {
    if (form.title && form.address && form.price && form.description) {
      setListings([...listings, form]);
      setForm({ title: '', address: '', price: '', description: '' });
    }
  };

  return (
    <div className="flex min-h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-white shadow-xl p-4 flex flex-col gap-4">
        <h2 className="text-2xl font-bold text-center text-blue-600">Seller Panel</h2>
        <nav className="flex flex-col gap-3 text-gray-700">
          <Button variant="ghost" className="justify-start"><Home className="mr-2" /> Dashboard</Button>
          <Button variant="ghost" className="justify-start"><Plus className="mr-2" /> Create Listing</Button>
          <Button variant="ghost" className="justify-start"><Bell className="mr-2" /> Notifications</Button>
          <Button variant="ghost" className="justify-start"><MessageCircle className="mr-2" /> Messages</Button>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 p-6 space-y-6">
        <h1 className="text-3xl font-semibold text-gray-800">Your Property Listings</h1>

        {/* Create Listing Form */}
        <Card className="p-6">
          <h2 className="text-xl font-semibold mb-4 text-blue-600">Create New Listing</h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Input name="title" placeholder="Property Title" value={form.title} onChange={handleInputChange} />
            <Input name="address" placeholder="Property Address" value={form.address} onChange={handleInputChange} />
            <Input name="price" placeholder="Price ($)" value={form.price} onChange={handleInputChange} />
            <Textarea name="description" placeholder="Property Description" value={form.description} onChange={handleInputChange} />
          </div>
          <Button className="mt-4" onClick={handleCreateListing}>Submit</Button>
        </Card>

        {/* Listings Overview */}
        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
          {listings.map((listing, index) => (
            <Card key={index} className="hover:shadow-lg transition duration-300">
              <CardContent className="p-4">
                <h3 className="text-lg font-bold text-gray-800">{listing.title}</h3>
                <p className="text-gray-600">{listing.address}</p>
                <p className="text-blue-500 font-semibold">${listing.price}</p>
                <p className="text-sm mt-2 text-gray-500">{listing.description}</p>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* Notifications and Messages */}
        <Tabs defaultValue="notifications" className="mt-6">
          <TabsList>
            <TabsTrigger value="notifications">Notifications</TabsTrigger>
            <TabsTrigger value="messages">Messages</TabsTrigger>
          </TabsList>
          <TabsContent value="notifications">
            <Card className="p-4 text-gray-700">No new notifications.</Card>
          </TabsContent>
          <TabsContent value="messages">
            <Card className="p-4 text-gray-700">No new messages.</Card>
          </TabsContent>
        </Tabs>
      </main>
    </div>
  );
}
