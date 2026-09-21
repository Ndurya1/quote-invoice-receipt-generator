import React, { useState } from "react";
import { Link } from "react-router-dom";
import logo from "../assets/Docu-logo.png";

export default function Header() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <>
     
      <div className="relative">
        <header className="flex justify-between mx-10 items-center pl-2 pr-2 top-0 bg-white/60 p-3  text-green-800 relative z-20 font-sans ">
          <div className="text-green-800 font-sans font-bold text-3xl flex justify-center items-center gap-0 tracking-tighter ">
            
            <img src={logo} alt="Logo" className="w-10 h-10 inline-block mr-2" />
            <a href="#Home">
              <h1>Docu<span className="text-black">Flow</span></h1>
            </a>

          </div>
          
         
          <ul className="hidden md:flex gap-10">
           
            <li className="flex justify-center items-center   px-4 rounded-lg bg-[#245C3A] text-[14px]  text-white ">
              <a href="#How-it-works">How It Works</a>
            </li>
            <li className="flex justify-center items-center   px-4 rounded-lg bg-[#245C3A] text-[14px]  text-white ">
              <a href="#Benefits">Benefits</a>
            </li>
            <li className="flex justify-center items-center   px-4 rounded-lg bg-[#245C3A] text-[14px]  text-white py-2">
              <a href="#Login">Login</a>
            </li>
           
          </ul>

        
          <div
            className="flex md:hidden justify-center items-center text-green-800 font-sans font-extrabold text-[25px] cursor-pointer  rounded-sm  px-2 py-1"
            onClick={() => setMenuOpen(!menuOpen)}
          >
            &#9776;
          </div>
        </header>

      
        <ul
          className={`
            md:hidden 
            flex flex-col 
            items-center 
            text-center
            absolute 
            top-full 
            left-0
            w-full m-auto 
            bg-green-800
            text-white 
            p-4 
            gap-3 
            transition-all duration-300 ease-in-out
            z-10
            ${menuOpen 
              ? "opacity-100 translate-y-0" 
              : "opacity-0 -translate-y-5 pointer-events-none"}
          `}
        >
          <a
            href="#How-it-works"
            className="hover:bg-white hover:text-green-800 text-[14px] font-sans w-full py-2 rounded-lg "
            onClick={() => setMenuOpen(false)} 
          >
            How It Works
          </a>

          <a
           className="hover:bg-white hover:text-green-800 text-[14px] font-sans w-full py-2 rounded-lg "
            href="#Benefits"
            onClick={() => setMenuOpen(false)}
          >
            Benefits
          </a>
          <a
            className="hover:bg-white hover:text-green-800 text-[14px] font-sans w-full py-2 rounded-lg "
            href="#Login"
            onClick={() => setMenuOpen(false)}
          >
            Login
          </a>
        
        </ul>
      </div>
    </>
  );
}
    
  

    
