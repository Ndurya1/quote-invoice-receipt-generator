import React from 'react';
import Header from '../components/Header';
import {ArrowRight, Dot} from 'lucide-react'
import smiling from '../assets/smiling-guy.jpg'
import logo from "../assets/Docu-logo.png";

export default function LandingPage() {
  return (
         
    <div> 
         <Header />

    <div className='mx-auto w-full max-w-[1200px] px-5 md:px-8 lg:px-12 xl:px-16 2xl:px-20'>
        <section>
            

             <div className=" pt-[48px] flex flex-col justify-center items-start lg:mb-28 mb-16   ">
                <p className='flex gap-2 text-xs font-bold text-green-700 '>QUOTES <ArrowRight className='h-4 w-4' /> INVOICES <ArrowRight className='h-4 w-4'/> RECEIPTS</p>

                <div className='flex flex-col justify-end items-start mb-4 gap-4 '>
                    <h1 className=' font-semibold md:font-bold font-sans md:text-[48px] text-[36px] text-[#182019] '>Create it once. <br/> 
                    <span className='text-green-700 '> Keep the paperwork moving.</span></h1>

                    <p className='flex flex-col items-start  max-w-sm text-[18px] pb-4 text-black '>Create professional quotes in minutes, then turn them into invoices and receipts -  without starting over.</p>
                </div>

                <div className="flex flex-col justify-start items-start gap-2 mb-4 ">
                    <button className='flex justify-center items-center gap-4 text-white bg-green-700 p-2 rounded-[8px] text-[14px]  font-medium  '>Create quotation <ArrowRight className='h-3 w-3'/> </button>
                    <p className='text-xs text-gray-600 '> Set up your business details once. We'll reuse them for your next document.</p>
                </div>
                

             </div>
        </section>

        <section className="grid grid-cols-1 lg:grid-cols-12 gap-4 lg:gap-12 lg:mb-28 mb-16 " >
            <div className="grid lg:col-span-8 gap-3 "> 
            <p className='flex gap-2 text-xs font-bold text-green-700 uppercase tracking-wider pb-2'> the problem</p>
            <h2 className="max-w-sm font-sans font-semibold text-[28px] " > Your invoice shouldn't start from a blank document every time.</h2>

            <p>You already entered your business details on the quotation. You already entered the client's details. You already listed the work and agreed on the price. So why enter everything again when it's time to invoice? </p>
            </div>

           <div className="grid lg:col-span-4"> 
                <img src={smiling} alt="Invoice" className="w-[300px]  rounded-lg  h-[300px]" />
            </div>

        </section>

        <section id='How-it-works'  className="flex flex-col justify-end items-start gap-4 lg:gap-12 lg:mb-28 mb-16 " >
            <div>
                <h2 className='flex gap-2 text-xs font-bold text-green-700 uppercase tracking-wider pb-2'>How it works</h2>
                <p className="max-w-sm font-sans font-semibold text-[28px] " > From quotation to receipt without starting over.</p>
            </div>

            <div  className="grid grid-cols-1 lg:grid-cols-12 gap-4  "> 
                <div className="grid lg:col-span-4  relative">
                    <h3 className="text-[18px] font-bold font-sans tracking-wide">Set up once</h3>
                    <p> Add your business details</p>
                    <p className="text-gray-600 text-[14px]" >Enter your business name, contact information and other details once. They'll be ready when you create your next document. </p>
                    <ArrowRight className="hidden lg:flex absolute top-12 right-0 w-5 h-5 text-gray-600  "/>
                </div>
                

                <div className="grid lg:col-span-4 gap-3 relative ">
                    <h3 className="text-[18px] font-bold font-sans tracking-wide">Create</h3>
                    <p> Fill in the job, not the paperwork</p>
                    <p className="text-gray-600 text-[14px]">Add your client, line items, quantities, prices, tax and discounts. Your totals are calculated for you. </p>
                     <ArrowRight className="hidden lg:flex absolute top-12 right-0 w-5 h-5 text-gray-600  "/>

                </div>
                

                <div className="grid lg:col-span-4 gap-3 ">
                    <h3 className="text-[18px] font-bold font-sans tracking-wide">Convert</h3>
                    <p > Keep the document moving</p>
                    <p className="text-gray-600 text-[14px]">Client approved the quotation? Convert it into an invoice. Once payment is recorded, use that invoice to create the receipt. </p>
                </div>

            </div>
        </section>

        <section id='Benefits'  className="grid grid-cols-1 lg:grid-cols-12 gap-4  lg:mb-28 mb-16 "> 
            <div className="grid lg:col-span-5"> 
                <p className='flex gap-2 text-xs font-bold text-green-700 uppercase tracking-wider '>Built for small businesses </p>
                <h2 className="max-w-sm font-sans font-semibold text-[28px] " >Less admin. More time for work </h2>
            </div>

            <div className=" grid lg:col-span-7 ">
                <div className="flex flex-col lg:flex-row gap-2 justify-center items-center pb-4" >
                <div> 
                    <p className="font-semibold font-sans " > Stop typing the same details</p>   
                    <p className="text-gray-600 text-[15px]" > Your business information is saved and reused across documents, so every quotation doesn't start from zero.</p> 
                </div>    
                <div> 
                    <p className="font-semibold font-sans "> Look professional from day one </p>   
                    <p className="text-gray-600 text-[15px]"> Create clean, consistent quotations, invoices and receipts without formatting documents manually. </p> 
                </div>  
             </div>

                <div className="flex flex-col lg:flex-row gap-2 lg:gap-12 justify-center items-center pb-4">
                <div> 
                    <p className="font-semibold font-sans ">  Let the numbers handle themselves </p>   
                    <p className="text-gray-600 text-[15px]"> Add quantities and prices, then let the system calculate subtotals, discounts, taxes and final totals. </p> 
                </div>    
                <div> 
                    <p className="font-semibold font-sans "> Keep related documents connected </p>   
                    <p className="text-gray-600 text-[15px]"> A quotation doesn't disappear once it's accepted. Carry its information forward into the invoice and receipt.</p> 
                </div>  
             </div>

            </div>

        </section>

        <section className="gap-4 lg:gap-12 lg:mb-28 mb-16"> 
            <div  className="max-w-xl font-sans flex flex-col justify-center items-center m-auto"> 

                <h2  className=" font-sans font-semibold text-[28px] " > Built for people who'd rather do the work than the paperwork</h2>
                <p > Freelancers, contractors and small service businesses don't always have someone dedicated to administration. <span className="font-semibold text-green-700">DocuFlow</span> keeps the basic document workflow simple enough to handle yourself.</p>
            </div>
            <p className="hidden lg:flex justify-center items-center text-green-700 m-2 mt-4 tracking-widest"> Freelancers <Dot className="w-12 h-12"/>  Designers <Dot className="w-12 h-12"/>  Developers <Dot className="w-12 h-12"/>  Consultants <Dot className="w-12 h-12"/>  Contractors <Dot className="w-12 h-12"/>  Service businesses</p>
        </section>

        <section className="gap-4  lg:mb-28 mb-16 justify-center items-center flex flex-col" >
            <p className='flex gap-2 text-xs font-bold text-green-700 uppercase tracking-wider pb-2'> Ready when you are</p>
            <h2 className=" font-sans font-semibold text-[28px] max-w-lg text-center" > Your next quotation can take minutes, not another Word document. </h2>
            <p> Set up your business details once and create your first quotation.</p>
            <button className='flex justify-center items-center gap-4 text-white bg-green-700 p-2 rounded-[8px] text-[14px]  font-medium  '>Create your first quotation <ArrowRight className='h-3 w-3'/> </button>
            <p className="text-xs text-gray-600 text-center"> Start with a quotation, invoice or receipt. No payment processing required.</p>

        </section>

        <footer className="gap-4 mb-3 grid lg:grid-cols-12  flex-col justify-center items-center "> 
                <div className="grid lg:col-span-5 justify-start items-start"> 
                     <div className="text-green-800 font-sans font-bold text-3xl flex justify-start items-start gap-0 tracking-tighter ">
                                
                        <img src={logo} alt="Logo" className="w-10 h-10 inline-block mr-2" />
                        <a href="#Home">
                            <h1>Docu<span className="text-black">Flow</span></h1>
                        </a>           
                    </div>
                    <p className="text-xs text-gray-600"> simple documents for people doing real work </p>
                    <p className="text-xs text-gray-600"> copyright &copy; {new Date().getFullYear()} All rights reserved</p>
                </div>

                <div className="grid lg:col-span-7 justify-end">
                    <ul className="flex gap-2 text-xs lg:text-sm items-center justify-center text-green-700 "> 
                        <li> <a href="/"> Home</a> </li> <Dot className="w-6 h-6"/> 
                        <li> <a href="/"> How It Works</a> </li><Dot className="w-6 h-6"/> 
                        <li> <a href="/"> Benefits</a> </li><Dot className="w-6 h-6"/> 
                        <li> <a href="/"> Login</a> </li>
                        
                    </ul>    
                </div>
        </footer>
     
      
    </div>
    </div>
  );
}