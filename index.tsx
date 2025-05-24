import React from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";

export default function SellerDashboard() {
  return (
    <div className="p-4 grid gap-6">
      <h1 className="text-2xl font-bold">Seller Dashboard</h1>

      <Tabs defaultValue="overview" className="w-full">
        <TabsList className="mb-4">
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="properties">My Listings</TabsTrigger>
          <TabsTrigger value="inquiries">Inquiries</TabsTrigger>
          <TabsTrigger value="analytics">Analytics</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <Card>
            <CardContent className="p-4">
              <h2 className="text-xl font-semibold mb-2">Welcome back!</h2>
              <p>You have 5 active listings and 3 new inquiries.</p>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="properties">
          <Card>
            <CardContent className="p-4">
              <h2 className="text-xl font-semibold mb-4">Your Properties</h2>
              <div className="grid gap-4">
                <div className="flex justify-between items-center p-3 border rounded-xl">
                  <div>
                    <p className="font-medium">123 Maple St, NY</p>
                    <p className="text-sm text-gray-500">Apartment - $1200/month</p>
                  </div>
                  <Button size="sm">Edit Listing</Button>
                </div>
                <div className="flex justify-between items-center p-3 border rounded-xl">
                  <div>
                    <p className="font-medium">456 Oak Ave, CA</p>
                    <p className="text-sm text-gray-500">House - $250,000</p>
                  </div>
                  <Button size="sm">Edit Listing</Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="inquiries">
          <Card>
            <CardContent className="p-4">
              <h2 className="text-xl font-semibold mb-4">Recent Inquiries</h2>
              <ul className="space-y-3">
                <li className="border p-3 rounded-xl">
                  <p className="font-medium">John Doe</p>
                  <p className="text-sm">"Is the apartment available for viewing next week?"</p>
                </li>
                <li className="border p-3 rounded-xl">
                  <p className="font-medium">Jane Smith</p>
                  <p className="text-sm">"Can you provide more pictures of the backyard?"</p>
                </li>
              </ul>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="analytics">
          <Card>
            <CardContent className="p-4">
              <h2 className="text-xl font-semibold mb-4">Listing Performance</h2>
              <ul className="space-y-2">
                <li>123 Maple St: 300 views, 5 inquiries</li>
                <li>456 Oak Ave: 450 views, 8 inquiries</li>
              </ul>
              <Button className="mt-4">Download Report</Button>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}
