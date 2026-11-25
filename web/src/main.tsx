import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import "./index.css";
import AdminApp from "./admin/AdminApp";
import MiniApp from "./miniapp/MiniApp";

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/admin/*" element={<AdminApp />} />
        <Route path="/*" element={<MiniApp />} />
      </Routes>
    </BrowserRouter>
  </React.StrictMode>,
);
