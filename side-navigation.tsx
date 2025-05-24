import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import { Bell, MessageSquare, Home, Plus } from "lucide-react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

const Sidebar = () => (
  <div className="w-64 h-screen bg-gray-800 text-white p-4">
    <h2 className="text-2xl font-bold mb-6">Seller Dashboard</h2>
    <nav className="flex flex-col gap-4">
      <Link to="/overview" className="flex items-center gap-2 hover:text-blue-400">
        <Home size={20} /> Listings Overview
      </Link>
      <Link to="/create" className="flex items-center gap-2 hover:text-blue-400">
        <Plus size={20} /> Create/Edit Listing
      </Link>
      <Link to="/notifications" className="flex items-center gap-2 hover:text-blue-400">
        <Bell size={20} /> Notifications
      </Link>
      <Link to="/messages" className="flex items-center gap-2 hover:text-blue-400">
        <MessageSquare size={20} /> Message Alerts
      </Link>
    </nav>
  </div>
);

const ListingsOverview = () => (
  <Card>
    <CardContent className="p-4">
      <h3 className="text-xl font-semibold mb-2">Your Property Listings</h3>
      <p>Total Active: 5</p>
      <p>Total Sold: 2</p>
      <p>Total Pending: 3</p>
    </CardContent>
  </Card>
);

const CreateEditListing = () => (
  <Card>
    <CardContent className="p-4">
      <h3 className="text-xl font-semibold mb-2">Create or Edit Your Listings</h3>
      <Button className="mt-2">Add New Listing</Button>
    </CardContent>
  </Card>
);

const Notifications = () => (
  <Card>
    <CardContent className="p-4">
      <h3 className="text-xl font-semibold mb-2">Notifications</h3>
      <ul className="list-disc pl-5">
        <li>New inquiry on 123 Main St</li>
        <li>Price update requested for 456 Park Ave</li>
      </ul>
    </CardContent>
  </Card>
);

const Messages = () => (
  <Card>
    <CardContent className="p-4">
      <h3 className="text-xl font-semibold mb-2">Messages</h3>
      <ul className="list-disc pl-5">
        <li>John Doe: Is the property still available?</li>
        <li>Jane Smith: Can I schedule a visit?</li>
      </ul>
    </CardContent>
  </Card>
);

const Dashboard = () => (
  <Router>
    <div className="flex">
      <Sidebar />
      <div className="flex-1 p-6">
        <Routes>
          <Route path="/overview" element={<ListingsOverview />} />
          <Route path="/create" element={<CreateEditListing />} />
          <Route path="/notifications" element={<Notifications />} />
          <Route path="/messages" element={<Messages />} />
        </Routes>
      </div>
    </div>
  </Router>
);

export default Dashboard;
