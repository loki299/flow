import React from "react";

class ChatSelect extends React.Component{
    constructor(props){
        super(props);
        this.state = {
            name: this.props.name,
            lastMsg: this.props.lastMsg,
            lastMsgTime: this.props.lastMsgTime,
            id: this.props.id
        };
        this.chid = this.handleClick.bind(this);
    }

    handleClick(){
        this.props.func_chid(this.state.id, this.state.name);
        // Notification.requestPermission();
        // new Notification(this.props.name);
    }

    render(){
        return (
            <div id={this.state.id} className="chat-select clickable" onClick={this.chid}>
                <h2>{this.state.name}</h2>
                {this.state.lastMsg && <h3>{this.state.lastMsg}</h3>}
            </div>
        );
    };
};

export default ChatSelect;